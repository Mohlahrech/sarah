# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning
from woocommerce import API
from odoo.tools import config
config['limit_time_real'] = 1000000

class Taxes(models.Model):
    _inherit = 'account.tax'

    woo_id = fields.Char('WooCommerce ID')
    woo_instance_id = fields.Many2one('woo.instance', ondelete='cascade')
    is_exported = fields.Boolean('Synced In Woocommerce', default=False)

    def cron_export_account_tax(self):
        all_instances = self.env['woo.instance'].sudo().search([])
        for rec in all_instances:
            if rec:
                self.env['account.tax'].export_selected_taxes(rec)

    def export_selected_taxes(self, instance_id):
        location = instance_id.url
        cons_key = instance_id.client_id
        sec_key = instance_id.client_secret
        version = 'wc/v3'

        wcapi = API(url=location,
                    consumer_key=cons_key,
                    consumer_secret=sec_key,
                    version=version
                    )

        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['account.tax'].sudo().browse(selected_ids)
        all_records = self.env['account.tax'].sudo().search([])
        if selected_records:
            records = selected_records
        else:
            records = all_records

        list = []
        for rec in records:
            list.append({
                "id": rec.woo_id,
                "name": rec.name,
                "rate": str(rec.amount),
            })

        if list:
            for data in list:
                if data.get('id') == False:
                    try:
                        wcapi.post("taxes", data).json()
                    except Exception as error:
                        raise UserError(_("Please check your connection and try again"))
                else:
                    try:
                        wcapi.post("taxes/" + data.get('id'), data).json()
                    except Exception as error:
                        raise UserError(_("Please check your connection and try again"))

        self.import_tax(instance_id)

    def cron_import_account_tax(self):
        all_instances = self.env['woo.instance'].sudo().search([])
        for rec in all_instances:
            if rec:
                self.env['account.tax'].import_tax(rec)

    def import_tax(self, instance_id):
        location = instance_id.url
        cons_key = instance_id.client_id
        sec_key = instance_id.client_secret
        version = 'wc/v3'
        page = 1

        wcapi = API(url=location, consumer_key=cons_key, consumer_secret=sec_key, version=version, timeout=400)

        url = "taxes"
        while page > 0:
            try:
                data = wcapi.get(url, params={'orderby': 'id', 'order': 'asc', 'per_page': 100, 'page': page})
                page += 1
            except Exception as error:
                raise UserError(_("Please check your connection and try again"))
            if data.status_code == 200 and data.content:
                parsed_data = data.json()
                if len(parsed_data) == 0:
                    page = 0
                if parsed_data:
                    for ele in parsed_data:
                        dict_tax = {}
                        tax_record = self.env['account.tax'].sudo().search([('woo_id', '=', ele.get('id')), ('name', '=', ele.get('name'))], limit=1)
                        tax_record_without_woo_id = self.env['account.tax'].search([('woo_id', '=', False), ('name', '=', ele.get('name'))], limit=1)
                        dict_tax['woo_instance_id'] = instance_id.id
                        dict_tax['company_id'] = instance_id.woo_company_id.id
                        dict_tax['is_exported'] = True
                        if ele.get('id'):
                            dict_tax['woo_id'] = ele.get('id')
                        if ele.get('name'):
                            dict_tax['name'] = ele.get('name')
                        if ele.get('rate'):
                            dict_tax['amount'] = ele.get('rate')
                        if not tax_record and tax_record_without_woo_id:
                            tax_record_without_woo_id.sudo().write(dict_tax)
                        if not tax_record and not tax_record_without_woo_id:
                            self.env['account.tax'].sudo().create(dict_tax)
                        else:
                            tax_record.sudo().write(dict_tax)
            else:
                page = 0

