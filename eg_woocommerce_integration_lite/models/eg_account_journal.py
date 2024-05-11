import logging
from odoo import fields, models
from odoo.exceptions import Warning

_logging = logging.getLogger("===+++ eCom Payment Gateway +++===")


class EgAccountJournal(models.Model):
    _inherit = 'eg.account.journal'

    description = fields.Text(string="Description")
    payment_order = fields.Integer(string="Order")
    is_payment_enable = fields.Boolean(string="Payment enable")
    payment_method_title = fields.Char(string="Payment Method")
    payment_method_description = fields.Text(string="Payment method description")

    def import_woo_payment_gateway(self, instance_id):
        """
        In this create odoo payment gateway and mapping payment gateway when import payment gateway.
        :param instance_id: Browseable object of instance
        :return: Nothing
        """
        woo_api = instance_id
        try:  # Changes by Akash
            wcapi = woo_api.get_wcapi_connection()
        except Exception as e:
            raise Warning("{}".format(e))
        payment_gateway_response = wcapi.get('payment_gateways')
        if payment_gateway_response.status_code == 200:  # Changes by Akash
            for woo_payment_gateway_dict in payment_gateway_response.json():
                eg_journal_id = self.search(
                    [("instance_payment_gateway_id", '=', str(woo_payment_gateway_dict.get("id"))),
                     ('instance_id', '=', woo_api.id)])
                odoo_account_journal_id = self.env['account.journal'].search(
                    [('name', '=', woo_payment_gateway_dict.get("title"))])

                if eg_journal_id and odoo_account_journal_id:
                    _logging.info(
                        "{} payment method is already created!!!".format(woo_payment_gateway_dict.get("title")))
                else:
                    if not odoo_account_journal_id:
                        odoo_account_journal_id = self.env['account.journal'].create({
                            'name': woo_payment_gateway_dict.get('title'),
                            'code': woo_payment_gateway_dict.get('title')[0:3].upper(),
                            'type': 'general', })
                    if not eg_journal_id:
                        self.create([{
                            'instance_id': woo_api.id,
                            'odoo_account_journal_id': odoo_account_journal_id.id,
                            'instance_payment_gateway_id': str(woo_payment_gateway_dict.get('id')),
                            'name': woo_payment_gateway_dict.get('title'),
                            'description': woo_payment_gateway_dict.get('description'),
                            'payment_order': woo_payment_gateway_dict.get('order'),
                            'is_payment_enable': woo_payment_gateway_dict.get('enabled'),
                            'payment_method_title': woo_payment_gateway_dict.get('method_title'),
                            'payment_method_description': woo_payment_gateway_dict.get('method_description'), }])
        else:
            raise Warning("{}".format(payment_gateway_response.text))
