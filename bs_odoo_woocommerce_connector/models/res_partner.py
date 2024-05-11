# -*- coding: utf-8 -*-
import base64
import logging
import urllib.request

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    woo_customer_role = fields.Char(string='Role', readonly=True, copy=False)
    woo_customer_id = fields.Integer('Woo Customer Id', readonly=True, copy=False)
    woo_user_name = fields.Char('Woo User Name', readonly=True, copy=False)
    is_guest = fields.Boolean('Guest User', default=False, readonly=True, copy=False)
    woo_instance_id = fields.Many2one('woo.configuration', 'Instance')

    def import_woo_customers(self, customer_datas, woo_instance):
        partner_data = self._prepare_customer_data(customer_datas, woo_instance)
        shipping_data = self._prepare_customer_data(customer_datas.get('shipping'), woo_instance, type='delivery',
                                                    woo_customer_id=customer_datas.get('id', ''))
        invoice_data = self._prepare_customer_data(customer_datas.get('billing'), woo_instance, type='invoice',
                                                   woo_customer_id=customer_datas.get('id', ''))
        try:
            partner_image = self.get_partner_image(customer_datas)
            if partner_image:
                partner_data.update({'image_1920': partner_image})
            partner_id = self.create(partner_data)
            shipping_data['parent_id'] = partner_id.id
            invoice_data['parent_id'] = partner_id.id
            shipping_id = self.create(shipping_data)
            invoice_id = self.create(invoice_data)
            if not shipping_id.name:
                shipping_id.name = partner_id.name + '(shipping address)'
            if not invoice_id.name:
                invoice_id.name = partner_id.name + '(invoice address)'
            return partner_id
        except Exception as e:
            raise UserError(_("%s") % e)

    def _prepare_customer_data(self, address, instance, type='contact', woo_customer_id=0):
        company_id = instance.company_id
        country_id = self._get_country_id(address.get('country'))
        state = False
        if country_id:
            state = self._get_create_state(country_id, address.get('state'))
        data = {
            "name": address.get('first_name', '') + address.get('last_name', ''),
            'street': address.get('address_1', ' '),
            'street2': address.get('address_2', ' '),
            'city': address.get('city', ''),
            'state_id': state,
            'zip': address.get('postcode', ''),
            'country_id': country_id,
            'email': address.get('email', ''),
            'mobile': address.get('phone', ''),
            'phone': address.get('phone', ''),
            'woo_customer_id': address.get('id', ''),
            'type': type,
            'company_id': company_id.id or False,
            'woo_customer_role': address.get('role', ''),
            'woo_user_name': address.get('username', ''),
            'woo_instance_id': instance.id
        }
        if not data.get('name'):
            data['name'] = address.get('username', '')
        if type != 'contact':
            data['woo_customer_id'] = woo_customer_id
        return data

    def _get_create_state(self, country, state):
        state_obj = self.env['res.country.state'].sudo()
        state_id = state_obj.search([('country_id', '=', country), ('code', '=', state)], limit=1)
        if not state_id:
            state_id = state_obj.create({
                'country_id': country,
                'code': state,
                'name': state
            })
            return state_id.id
        return state_id.id

    def _get_country_id(self, country_code):
        country_obj = self.env['res.country'].sudo()
        country_id = country_obj.search([('code', '=', country_code)], limit=1)
        return country_id.id if country_id else False

    def get_partner_image(self, customer_data):
        try:
            product_image_1920 = customer_data.get('avatar_url')
            if product_image_1920:
                image_url = product_image_1920
                image = urllib.request.urlopen(image_url).read()
                product_image_1920 = base64.b64encode(image)

            return product_image_1920
        except Exception as e:
            raise UserError(_("%s") % e)

    @api.model
    def _get_create_partner_by_id(self, customer_id, wcapi, woo_instance):
        log_obj = self.env['synchronization.log']
        try:
            customer_res = wcapi.get('customers/{}'.format(customer_id))
            customer = customer_res.json()
            partner_id = self.import_woo_customers(customer_datas=customer, woo_instance=woo_instance)
            log_obj.sudo().create({
                'operation_type': 'import',
                'operation_on': 'customer',
                'status_code': customer_res.status_code,
                'method': customer_res.request.method,
                'url': customer_res.url,
                'model': self._name,
                'message': customer_res.text,
                'company_id': woo_instance.company_id.id
            })
            return partner_id.id
        except Exception as e:
            log_obj.sudo().create({
                'operation_type': 'import',
                'operation_on': 'customer',
                'status_code': '',
                'method': '',
                'url': '',
                'model': self._name,
                'message': str(e),
                'company_id': woo_instance.company_id.id
            })
