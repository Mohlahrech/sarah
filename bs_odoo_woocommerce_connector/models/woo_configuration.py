# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from woocommerce import API

from odoo import models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WooConfiguration(models.Model):
    _name = 'woo.configuration'
    _description = 'Woocommerce Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"

    _sql_constraints = [
        (
            "company_id__uniq",
            "UNIQUE(company_id)",
            "Each Company can have one Instance."
        )
    ]

    name = fields.Char(string='Name')
    state = fields.Selection(selection=[('draft', 'Draft'), ('validate', 'Validated')], default='draft', copy=False)
    consumer_key = fields.Char('Consumer Key', required=True)
    consumer_secret = fields.Char('Consumer Secret', required=True)
    Url = fields.Char('Store Url', required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, required=True)
    last_product_import_date = fields.Datetime('Last Product Import Date')
    last_customer_import_date = fields.Datetime('Last Customer Import Date', copy=False)
    last_customer_import_page = fields.Integer('Last Customer Import Page Number', default=1)
    last_order_import_date = fields.Datetime('Last Order Import Date')
    order_status = fields.Selection([
        ('any', 'Any'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('on-hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
        ('trash', 'Trash'),
    ], 'Order Status')
    import_all_order = fields.Boolean('Import All Orders', default=True)

    def import_orders_cron(self):
        for rec in self.search([('state', '=', 'validate')]):
            rec.with_context(context='cron').import_woo_orders()

    def import_customers_cron(self):
        for rec in self.search([('state', '=', 'validate')]):
            rec.with_context(context='cron').import_customers()

    def import_product_category_cron(self):
        for rec in self.search([('state', '=', 'validate')]):
            rec.with_context(context='cron').product_categories_import()

    def import_product_attributes_cron(self):
        for rec in self.search([('state', '=', 'validate')]):
            rec.with_context(context='cron').import_product_attrs()

    def import_products_cron(self):
        for rec in self.search([('state', '=', 'validate')]):
            rec.with_context(context='cron').import_woo_products()

    def import_shipping_methods_cron(self):
        for rec in self.search([('state', '=', 'validate')]):
            rec.with_context(context='cron').import_shipping_methods()

    def import_tax_cron(self):
        for rec in self.search([('state', '=', 'validate')]):
            rec.with_context(context='cron').tax_rate_import()

    def action_validate(self):
        self.ensure_one()
        success = self._authenticate(validate=True)
        if not success:
            raise UserError('Wrong Configuration setup for {}'.format(self.name))
        else:
            self.state = 'validate'

    def set_to_draft(self):
        self.ensure_one()
        self.state = 'draft'

    def _authenticate(self, validate=False):
        wcapi = API(
            url=self.Url,
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret
        )
        try:
            response = wcapi.get('products', params={'per_page': 1})
            if response.status_code == 200:
                return wcapi
            else:
                if validate:
                    return False
                raise UserError(_("Error") % response)
        except Exception as e:
            if validate:
                return False
            raise UserError(_("%s") % e)

    def product_categories_import(self):
        wcapi = self._authenticate()
        self.env['product.category'].bulk_category(wcapi, instance=self)
        if not self._context.get('context') == 'cron':
            return self.popup_msg()

    def tax_rate_import(self):
        wcapi = self._authenticate()
        self.env['account.tax'].get_tax_batch(wcapi=wcapi, instance=self)
        if not self._context.get('context') == 'cron':
            return self.popup_msg()

    def import_product_attrs(self):
        wcapi = self._authenticate()
        self.env['product.attribute'].create_product_attribute(wcapi, instance=self)
        if not self._context.get('context') == 'cron':
            return self.popup_msg()

    def import_woo_products(self):
        wcapi = self._authenticate()
        log_obj = self.env['synchronization.log']
        last_import_date = self.last_product_import_date.strftime(
            "%Y-%m-%dT%H:%M:%S") if self.last_product_import_date else False
        per_page = 20
        failed_ids = []
        try:
            response = wcapi.get('products', params={'order': 'asc', "after": last_import_date, 'per_page': per_page,
                                                     'status': 'publish'}) \
                if last_import_date else wcapi.get('products',
                                                   params={'order': 'asc', 'per_page': per_page, 'status': 'publish'})
            product_datas = response.json()
            for product_data in product_datas:
                prod = self.env['product.template']._create_product(data=product_data, wcapi=wcapi, instance=self)
                if not prod:
                    failed_ids.append(product_data.get('id'))
                    continue
                product_created_time = product_data.get('date_created_gmt')
                self.last_product_import_date = datetime.strptime(product_created_time, '%Y-%m-%dT%H:%M:%S')

            log_obj.create({
                'operation_type': 'import',
                'operation_on': 'product',
                'status_code': response.status_code,
                'method': response.request.method,
                'url': response.url,
                'model': self._name,
                'message': response.text,
                'failed_ids': failed_ids or '',
                'company_id': self.company_id.id
            })
            if not self._context.get('context') == 'cron':
                return self.popup_msg()

        except Exception as e:
            log_obj.sudo().create({
                'operation_type': 'import',
                'operation_on': 'product',
                'status_code': '',
                'method': '',
                'url': '',
                'model': self._name,
                'message': str(e),
                'company_id': self.company_id.id
            })

    def import_customers(self):
        log_obj = self.env['synchronization.log']
        wcapi = self._authenticate()
        customer_obj = self.env["res.partner"]
        customer_datas = []
        page_number = self.last_customer_import_page
        customer_ids = []
        customer_req = 1
        failed_ids = []
        max_req = 1
        per_page = 10
        try:
            woo_last_import_customer = customer_obj.search(
                [("woo_instance_id", "=", self.id), ('woo_customer_id', '>', 0)], order='woo_customer_id desc',
                limit=1)
            while True:
                response = wcapi.get('customers', params={"per_page": per_page, 'page': page_number, "orderby": "id",
                                                          'role': 'all'})
                customer_res = response.json()
                if len(customer_res) == per_page:
                    page_number += 1
                for customer in customer_res[::-1]:
                    if woo_last_import_customer and customer['id'] <= woo_last_import_customer.woo_customer_id:
                        break
                    if customer['id'] not in customer_ids:
                        customer_datas.append(customer)
                        customer_ids.append(customer['id'])
                customer_req += 1
                if customer_req >= max_req or not customer_res or not customer_datas:
                    break
            self.last_customer_import_page = page_number
            for customer in customer_datas:
                partner = self.env['res.partner'].import_woo_customers(customer, self)
                if not partner:
                    failed_ids.append(customer['id'])
            self.last_customer_import_date = datetime.now()

            log_obj.create({
                'operation_type': 'import',
                'operation_on': 'customer',
                'status_code': response.status_code,
                'method': response.request.method,
                'url': response.url,
                'model': self._name,
                'message': response.text,
                'failed_ids': failed_ids or '',
                'company_id': self.company_id.id
            })
            if not self._context.get('context') == 'cron':
                return self.popup_msg()
        except Exception as e:
            log_obj.create({
                'operation_type': 'import',
                'operation_on': 'customer',
                'status_code': '',
                'method': '',
                'url': '',
                'model': self._name,
                'message': str(e),
                'company_id': self.company_id.id
            })
        return True

    def import_woo_orders(self):
        wcapi = self._authenticate()
        log_obj = self.env['synchronization.log']
        last_import_date = self.last_order_import_date.strftime(
            "%Y-%m-%dT%H:%M:%S") if self.last_order_import_date else False
        per_page = 20
        params = {'per_page': per_page, 'order': 'asc'}
        if last_import_date and self.import_all_order:
            params['after'] = last_import_date
        elif not self.import_all_order:
            params['status'] = self.order_status
            if last_import_date:
                params['after'] = last_import_date
        try:
            order_res = wcapi.get('orders', params=params)
            order_datas = order_res.json()
            failed_ids = []
            for order_data in order_datas:
                so = self.env['sale.order']._create_woo_sale_order(wcapi=wcapi, order=order_data, woo_instance=self)
                if not so:
                    failed_ids.append(order_data.get('id'))
                self.last_order_import_date = datetime.strptime(order_data.get('date_created_gmt'), '%Y-%m-%dT%H:%M:%S')
            log_obj.create({
                'operation_type': 'import',
                'operation_on': 'order',
                'status_code': order_res.status_code,
                'method': order_res.request.method,
                'url': order_res.url,
                'model': self._name,
                'message': order_res.text,
                'failed_ids': failed_ids or '',
                'company_id': self.company_id.id
            })
            if not self._context.get('context') == 'cron':
                return self.popup_msg()
        except Exception as e:
            log_obj.create({
                'operation_type': 'import',
                'operation_on': 'order',
                'status_code': '',
                'method': '',
                'url': '',
                'model': self._name,
                'message': str(e),
                'company_id': self.company_id.id
            })

    def import_shipping_methods(self):
        wcapi = self._authenticate()
        self.env['delivery.carrier']._create_shipping_method(wcapi=wcapi, instance=self)
        if not self._context.get('context') == 'cron':
            return self.popup_msg()

    def popup_msg(self, success=True, error=''):
        return {
            'res_model': 'woo.configuration',
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'info',
                'title': _("Info"),
                'message': _('Completed') if success else _('Failed.\n{}'.format(error)),
            }
        }
