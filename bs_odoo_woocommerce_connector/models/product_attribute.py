# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    woo_att_id = fields.Char('Woo Id', readonly=True, copy=False)

    @api.model
    def create_product_attribute(self, wcapi, instance):
        log_obj = self.env['synchronization.log']
        try:
            failed_ids = []
            prod_att_res = wcapi.get("products/attributes")
            if prod_att_res.status_code == 200:
                prod_att = prod_att_res.json()
                for att in prod_att:
                    existing_att = self.search_read([('woo_att_id', '=', att.get('id'))], limit=1)
                    if not len(existing_att):
                        vals = self._get_prod_att_vals(data=att, wcapi=wcapi, instance=instance)
                        attribute = self.create(vals) if vals else False
                        if not attribute:
                            failed_ids.append(att.get('id'))
            log_obj.sudo().create({
                'operation_type': 'import',
                'operation_on': 'attribute',
                'status_code': prod_att_res.status_code,
                'method': prod_att_res.request.method,
                'url': prod_att_res.url,
                'model': self._name,
                'message': prod_att_res.text,
                'failed_ids': failed_ids or '',
                'company_id': instance.company_id.id
            })
        except Exception as e:
            log_obj.sudo().create({
                'operation_type': 'import',
                'operation_on': 'attribute',
                'status_code': '',
                'method': '',
                'url': '',
                'model': self._name,
                'message': str(e),
                'company_id': instance.company_id.id
            })

    def _get_prod_att_vals(self, data, wcapi, instance):
        return {
            'name': data.get('name'),
            'woo_att_id': data.get('id'),
            'display_type': data.get('type'),
            'value_ids': self._get_woo_prod_att_value_lines(wcapi=wcapi, att_id=data.get('id'), instance=instance)
        }

    def _get_woo_prod_att_value_lines(self, att_id, wcapi, instance):
        val_ids = []
        log_obj = self.env['synchronization.log']
        try:
            att_terms_res = wcapi.get("products/attributes/{}/terms".format(att_id))
            if att_terms_res.status_code == 200:
                att_val = att_terms_res.json()
                for terms in att_val:
                    val_ids.append((0, 0,
                                    {'name': terms.get('name')}
                                    ))
            log_obj.sudo().create({
                'operation_type': 'import',
                'operation_on': 'attribute',
                'status_code': att_terms_res.status_code,
                'method': att_terms_res.request.method,
                'url': att_terms_res.url,
                'model': self._name,
                'message': att_terms_res.text,
                'company_id': instance.company_id.id
            })
        except Exception as e:
            log_obj.sudo().create({
                'operation_type': 'import',
                'operation_on': 'category',
                'status_code': '',
                'method': '',
                'url': '',
                'model': self._name,
                'message': str(e),
                'company_id': instance.company_id.id
            })
        return val_ids

    def _get_product_attribute_line_values(self, data, wcapi, instance):
        vals = []
        for rec in data:
            existing_att_id = self.search_read([('woo_att_id', '=', rec.get('id'))])
            att_id = self._get_or_create_att_by_id(att_id=rec.get('id'),
                                                   wcapi=wcapi, instance=instance).id if not existing_att_id else existing_att_id[0]['id']
            att_values = self.env['product.attribute.value'].search([('name', 'in', rec.get('options'))])
            vals.append((0, 0,
                         {'attribute_id': att_id,
                          'value_ids': att_values.ids}
                         ))
        return vals

    @api.model
    def _get_or_create_att_by_id(self, att_id, wcapi, instance):
        try:
            woo_att_res = wcapi.get("products/attributes/{}".format(att_id))
            if woo_att_res.status_code == 200:
                woo_att = woo_att_res.json()
                vals = self._get_prod_att_vals(data=woo_att, wcapi=wcapi, instance=instance)
                attribute = self.create(vals)
                return attribute
        except Exception as e:
            raise UserError(_("%s") % e)
        return False
