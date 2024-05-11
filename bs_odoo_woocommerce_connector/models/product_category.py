from odoo import models, fields, api, _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    woo_id = fields.Integer('Woo Category Id', readonly=True, copy=False)

    @staticmethod
    def woo_to_odoo(datas):
        return {
            'name': datas.get('name'),
            'woo_id': datas.get('id'),
            'parent_id': datas.get('parent') or False
        }

    @staticmethod
    def odoo_to_woo(datas):
        # todo: future work
        pass

    @api.model
    def _get_woo_category_by_id(self, wcapi, id, instance):
        log_obj = self.env['synchronization.log']
        try:
            response = wcapi.get('products/categories/{}'.format(id))
            data = response.json()
            log_obj.sudo().create({
                'operation_type': 'import',
                'operation_on': 'category',
                'status_code': response.status_code,
                'method': response.request.method,
                'url': response.url,
                'model': self._name,
                'message': response.text,
                'company_id': instance.company_id.id
            })
            return data
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

    @api.model
    def _create_woo_cat(self, data, wcapi, instance):
        existing_categ = self.search_read(domain=[('woo_id', '=', data.get('id'))], fields=['id'])
        if not existing_categ:
            parent = data.get('parent')
            if parent != 0:
                existing_parent_cat_id = self.search_read(domain=[('woo_id', '=', parent)], fields=['id'])
                if not existing_parent_cat_id:
                    parent_cat_data = self._get_woo_category_by_id(wcapi=wcapi, id=data['parent'], instance=instance)
                    parent_cat_id = self._create_woo_cat(data=parent_cat_data, wcapi=wcapi, instance=instance)
                else:
                    parent_cat_id = existing_parent_cat_id[0]['id']
                data.update({'parent': parent_cat_id})
            cat_id = self.create(self.woo_to_odoo(data))
            return cat_id.id
        return existing_categ[0]['id']

    @api.model
    def _get_or_create_category_id(self, woo_categories, wcapi, instance):
        category_id = max(woo_categories, key=lambda x: x['id'])['id']
        odoo_category = self.env['product.category'].search_read([('woo_id', '=', category_id)], ['id'])
        if odoo_category:
            return odoo_category[0]['id']
        else:
            woo_category = self._get_woo_category_by_id(wcapi=wcapi, id=category_id, instance=instance)
            odoo_category_id = self._create_woo_cat(data=woo_category, wcapi=wcapi, instance=instance)
            return odoo_category_id

    def bulk_category(self, wcapi, instance):
        log_obj = self.env['synchronization.log']
        try:
            response = wcapi.get('products/categories')
            datas = response.json()
            for data in datas:
                self._create_woo_cat(data=data, wcapi=wcapi, instance=instance)
            log_obj.sudo().create({
                'operation_type': 'import',
                'operation_on': 'category',
                'status_code': response.status_code,
                'method': response.request.method,
                'url': response.url,
                'model': self._name,
                'message': response.text,
                'company_id': instance.company_id.id
            })
        except Exception as e:
            log_obj.sudo().create({
                'operation_type': 'import',
                'operation_on': 'category',
                'status_code': '',
                'method': '',
                'url': e.request.url,
                'model': self._name,
                'message': str(e),
                'company_id': instance.company_id.id
            })
