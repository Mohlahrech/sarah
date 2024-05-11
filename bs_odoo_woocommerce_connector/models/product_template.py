# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    woo_product_id = fields.Integer('Woo Product Id')
    regular_price = fields.Float('Woo Standard Price')
    sale_price = fields.Float('Woo Sale Price')
    woo_sku = fields.Char('Sku')

    @api.model
    def _create_product(self, data, wcapi, instance):
        existing_product_id = self.search_read(domain=[('woo_product_id', '=', data.get('id'))], fields=['id'])
        if not existing_product_id:
            product_create_vals = self._get_product_dict(data=data, wcapi=wcapi, instance=instance)
            prod = self.create(product_create_vals) if product_create_vals else False
            return prod.id if prod else False
        return existing_product_id[0]['id']

    def _get_product_dict(self, data, wcapi, instance):
        attributes = data.get('attributes')
        if data.get('type') in ['simple', 'variable']:
            if data.get('type') == 'simple' and not data.get('manage_stock'):
                odoo_product_type = 'consu'
            else:
                odoo_product_type = 'product'
        else:
            return
        odoo_category = self.env['product.category']._get_or_create_category_id(
            woo_categories=data.get('categories'), wcapi=wcapi, instance=instance) if data.get('categories') else False

        attribute_lines = self.env['product.attribute']._get_product_attribute_line_values(data=attributes,
                                                                                           wcapi=wcapi, instance=instance) if attributes else False
        vals = {
            'name': data.get('name'),
            'detailed_type': odoo_product_type,
            'woo_sku': data.get('sku'),
            'list_price': data.get('sale_price') or data.get('price'),
            'standard_price': data.get('price', 0),
            'categ_id': odoo_category,
            'attribute_line_ids': attribute_lines,
            'description': data.get('description'),
            'weight': float(data.get('weight')) if data.get('weight') else '',
            'purchase_ok': data.get('purchasable', True),
            'description_purchase': data.get('purchase_note'),
            'taxes_id': [],
            'supplier_taxes_id': [],
            'woo_product_id': data.get('id'),
            'regular_price': data.get('regular_price'),
            'sale_price': data.get('sale_price'),
        }
        return vals

    @api.model
    def _get_create_product_by_id(self, wcapi, id, instance):
        log_obj = self.env['synchronization.log']
        try:
            prod_data = wcapi.get('products/{}'.format(id))
            if prod_data.status_code == 200:
                prod = self._create_product(data=prod_data.json(), wcapi=wcapi, instance=instance)
                return prod
            return False
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
