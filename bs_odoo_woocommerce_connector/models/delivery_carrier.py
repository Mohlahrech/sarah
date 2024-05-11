# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    woo_shipping_method_id = fields.Char('Woo Shipping Method Id', readonly=True, copy=False)

    @api.model
    def _create_shipping_method(self, wcapi,instance):
        log_obj = self.env['synchronization.log']
        try:
            failed_ids = []
            methods_res = wcapi.get('shipping_methods')
            methods = methods_res.json()
            for method in methods:
                existing_method = self.search_read([('woo_shipping_method_id', '=', method.get('id'))])
                if not len(existing_method):
                    shp_method = self.create((self._get_shipping_method_create_dict(method=method)))
                    if not shp_method:
                        failed_ids.append(method.get('id'))
            log_obj.sudo().create({
                'operation_type': 'import',
                'operation_on': 'shipping_method',
                'status_code': methods_res.status_code,
                'method': methods_res.request.method,
                'url': methods_res.url,
                'model': self._name,
                'message': methods_res.text,
                'failed_ids': failed_ids or '',
                'company_id': instance.company_id.id
            })
        except Exception as e:
            log_obj.sudo().create({
                'operation_type': 'import',
                'operation_on': 'shipping_method',
                'status_code': '',
                'method': '',
                'url': '',
                'model': self._name,
                'message': str(e),
                'company_id': instance.company_id.id
            })

    @api.model
    def _get_or_create_carrier_by_method_id(self, wcapi, method_id, instance):
        log_obj = self.env['synchronization.log']
        try:
            carrier_res = wcapi.get('shipping_methods/{}'.format(method_id))
            if carrier_res.status_code == 200:
                carrier_info = carrier_res.json()
                carrier = self.create(self._get_shipping_method_create_dict(method=carrier_info))
                return carrier
            log_obj.sudo().create({
                'operation_type': 'import',
                'operation_on': 'shipping_method',
                'status_code': carrier_res.status_code,
                'method': carrier_res.request.method,
                'url': carrier_res.url,
                'model': self._name,
                'message': carrier_res.text,
                'company_id': instance.company_id.id
            })
            return False
        except Exception as e:
            log_obj.sudo().create({
                'operation_type': 'import',
                'operation_on': 'shipping_method',
                'status_code': '',
                'method': '',
                'url': '',
                'model': self._name,
                'message': str(e),
                'company_id': instance.company_id.id
            })

    def _get_shipping_method_create_dict(self, method):
        product = self.env['product.product'].search_read([('default_code', '=', 'Delivery_007')])
        return {
            'name': method.get('title'),
            'product_id': product[0]['id'],
            'woo_shipping_method_id': method.get('id'),
        }
