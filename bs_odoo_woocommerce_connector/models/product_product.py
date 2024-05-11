from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    woo_variation_id = fields.Integer('Woo Variation Id')

    def _get_or_create_product_id(self, line, wcapi, instance):
        product_tmpl = self.env['product.template']
        product_tmpl._get_create_product_by_id(
                wcapi=wcapi, id=line.get('product_id'), instance=instance)
        if line.get('variation_id'):
            existing_product_variant = self.search_read(
                [('woo_variation_id', '=', line.get('variation_id'))])
            product_id = existing_product_variant[0]['id'] if existing_product_variant else \
                self._get_product_variation(wcapi=wcapi, woo_prod_id=line.get('product_id'),
                                            woo_variation_id=line.get('variation_id'), instance=instance)
        else:
            existing_product = self.search_read(
                [('woo_product_id', '=', line.get('product_id'))], limit=1)
            product_id = existing_product[0]['id'] if existing_product else False
        return product_id

    def _get_product_variation(self, wcapi, woo_prod_id, woo_variation_id, instance):
        log_obj = self.env['synchronization.log']
        try:
            variant_res = wcapi.get('products/{}/variations/{}'.format(woo_prod_id, woo_variation_id))
            variant_data = variant_res.json() if variant_res.status_code == 200 else False
            if variant_data:
                woo_prod_variant_atts = variant_data.get('attributes')
                woo_variant_att_values = [d.get('option', None) for d in woo_prod_variant_atts]
                prod_variants = self.search([('woo_product_id', '=', woo_prod_id)])
                variant = prod_variants.filtered(lambda t: t.product_template_attribute_value_ids.mapped('name') == woo_variant_att_values)
                if variant:
                    variant.woo_variation_id = woo_variation_id
                    return variant.id
            log_obj.sudo().create({
                'operation_type': 'import',
                'operation_on': 'product',
                'status_code': variant_res.status_code,
                'method': variant_res.request.method,
                'url': variant_res.url,
                'model': self._name,
                'message': variant_res.text,
                'company_id': instance.company_id.id
            })
            return False
        except Exception as e:
            log_obj.sudo().create({
                'operation_type': 'import',
                'status_code': '',
                'method': '',
                'url': '',
                'model': self._name,
                'message': str(e),
                'company_id': instance.company_id.id
            })
