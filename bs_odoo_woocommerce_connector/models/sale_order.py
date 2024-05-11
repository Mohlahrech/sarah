# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    woo_instance_id = fields.Many2one('woo.configuration', 'Woo Instance')
    woo_order_id = fields.Integer('Woo Order Id', copy=False, readonly=True)
    is_woo_order = fields.Boolean('Is Woo Order', default=False)
    woo_create_date = fields.Datetime('Woo Order Create Date', copy=False, readonly=True)

    billing_first_name = fields.Char('First Name', copy=False, readonly=True)
    billing_last_name = fields.Char('Last Name', copy=False, readonly=True)
    billing_company = fields.Char('First Name', copy=False, readonly=True)
    billing_address1 = fields.Char('Address1', copy=False, readonly=True)
    billing_address2 = fields.Char('Address2', copy=False, readonly=True)
    billing_city = fields.Char('City', copy=False, readonly=True)
    billing_state = fields.Char('First Name', copy=False, readonly=True)
    billing_postcode = fields.Char('Postcode', copy=False, readonly=True)
    billing_country_iso = fields.Char('Country', copy=False, readonly=True)
    billing_email = fields.Char('Email', copy=False, readonly=True)
    billing_phone = fields.Char('Phone', copy=False, readonly=True)

    shipping_first_name = fields.Char('First Name', copy=False, readonly=True)
    shipping_last_name = fields.Char('Last Name', copy=False, readonly=True)
    shipping_company = fields.Char('First Name', copy=False, readonly=True)
    shipping_address1 = fields.Char('Address1', copy=False, readonly=True)
    shipping_address2 = fields.Char('Address2', copy=False, readonly=True)
    shipping_city = fields.Char('City', copy=False, readonly=True)
    shipping_state = fields.Char('First Name', copy=False, readonly=True)
    shipping_postcode = fields.Char('Postcode', copy=False, readonly=True)
    shipping_country_iso = fields.Char('Country', copy=False, readonly=True)
    shipping_email = fields.Char('Email', copy=False, readonly=True)
    shipping_phone = fields.Char('Phone', copy=False, readonly=True)

    @staticmethod
    def _get_billing_and_shipping_details(billing_address, shipping_address):
        return {
            'billing_first_name': billing_address.get('first_name', ''),
            'billing_last_name': billing_address.get('last_name', ''),
            'billing_address1': billing_address.get('address_1', ' '),
            'billing_address2': billing_address.get('address_2', ' '),
            'billing_city': billing_address.get('city', ''),
            'billing_state': billing_address.get('state', ''),
            'billing_postcode': billing_address.get('postcode', ''),
            'billing_country_iso': billing_address.get('country', ''),
            'billing_email': billing_address.get('email', ''),
            'billing_phone': billing_address.get('phone', ''),
            'billing_company': billing_address.get('company', ''),

            'shipping_first_name': shipping_address.get('first_name', ''),
            'shipping_last_name': shipping_address.get('last_name', ''),
            'shipping_address1': shipping_address.get('address_1', ' '),
            'shipping_address2': shipping_address.get('address_2', ' '),
            'shipping_city': shipping_address.get('city', ''),
            'shipping_state': shipping_address.get('state', ''),
            'shipping_postcode': shipping_address.get('postcode', ''),
            'shipping_country_iso': shipping_address.get('country', ''),
            'shipping_email': shipping_address.get('email', ''),
            'shipping_phone': shipping_address.get('phone', ''),
            'shipping_company': shipping_address.get('company', ''),
        }

    @api.model
    def _create_woo_sale_order(self, wcapi, order, woo_instance):
        existing_order = self.search_read(
            [('woo_order_id', '=', order.get('id')), ('woo_instance_id', '=', woo_instance.id)])
        if not existing_order:
            vals = self._get_sale_order_create_dict(order_data=order, woo_instance=woo_instance,
                                                    wcapi=wcapi)
            billing_and_shipping_details = self._get_billing_and_shipping_details(billing_address=order.get('billing'),
                                                                                  shipping_address=order.get(
                                                                                      'shipping'))
            if not vals:
                return False
            vals.update(billing_and_shipping_details)
            so = self.create(vals)
            return so if so else False
        return True

    def _get_sale_order_create_dict(self, order_data, woo_instance, wcapi):
        partner_obj = self.env['res.partner']
        order_lines = self._get_so_order_lines(line_items=order_data.get('line_items'), wcapi=wcapi,
                                               instance=woo_instance)
        shipping_lines = order_data.get('shipping_lines')
        if shipping_lines:
            delivery_lines = self._get_delivery_line(shipping_lines=shipping_lines,
                                                     instance=woo_instance, wcapi=wcapi)
            if delivery_lines:
                order_lines.append((0, 0, delivery_lines))
        datetime_order = datetime.strptime(order_data.get('date_created_gmt'), '%Y-%m-%dT%H:%M:%S')
        customer = order_data.get('customer_id')
        if customer > 0:
            existing_partner = partner_obj.search_read([('woo_customer_id', '=', customer)])
            partner = existing_partner[0]['id'] if existing_partner else partner_obj._get_create_partner_by_id(
                customer_id=customer, woo_instance=woo_instance, wcapi=wcapi)
        else:
            partner = self.env.ref('bs_odoo_woocommerce_connector.guest_partner').id

        return {
            'company_id': woo_instance.company_id.id,
            'partner_id': partner,
            'woo_create_date': datetime_order,
            'name': self.env['ir.sequence'].next_by_code('WC.order') or False,
            'order_line': order_lines,
            'is_woo_order': True,
            'woo_instance_id': woo_instance.id,
            'woo_order_id': order_data.get('id')
        } if order_lines else False

    def _get_so_order_lines(self, line_items, wcapi, instance):
        product_obj = self.env['product.product']
        tax_obj = self.env['account.tax']
        order_line_vals = []
        for line in line_items:
            product_id = product_obj._get_or_create_product_id(line=line, wcapi=wcapi, instance=instance)
            tax_ids = tax_obj._get_tax_ids(line.get('taxes'))
            order_line_vals.append((0, 0, {
                'product_id': product_id,
                'price_unit': line.get('price'),
                'name': line.get('name'),
                'product_uom_qty': line.get('quantity'),
                'tax_id': [(6, 0, tax_ids)] if tax_ids else []
            })) if product_id else False
        return order_line_vals

    def _get_delivery_line(self, wcapi, shipping_lines, instance):
        tax_obj = self.env['account.tax']
        vals = []
        method_id = shipping_lines[0]['method_id']
        if not method_id == '':
            carrier = self.env['delivery.carrier'].search([('woo_shipping_method_id', '=', method_id)])
            carrier_id = carrier if carrier else \
                self.env['delivery.carrier']._get_or_create_carrier_by_method_id(
                    wcapi=wcapi, method_id=method_id, instance=instance)
            product_id = carrier_id.product_id.id
            name = carrier_id.name
            shipping_price = shipping_lines[0]['total']
            tax_ids = tax_obj._get_tax_ids(shipping_lines[0]['taxes'])
            vals = {
                'product_id': product_id,
                'price_unit': shipping_price,
                'name': name,
                'product_uom_qty': 1,
                'tax_id': [(6, 0, tax_ids)] if tax_ids else []
            }
        return vals
