# -*- coding: utf-8 -*-
import imghdr
import urllib
import base64
import requests
import json
import itertools
import logging
import time
from woocommerce import API
from urllib.request import urlopen
from odoo.exceptions import UserError
from odoo import models, api, fields, _
from odoo.tools import config
from bs4 import BeautifulSoup
config['limit_time_real'] = 1000000


_logger = logging.getLogger(__name__)

class WooProductImage(models.Model):
    _name = 'woo.product.image'
    _description = 'woo.product.image'

    name = fields.Char()
    product_id = fields.Many2one('product.product', ondelete='cascade')
    template_id = fields.Many2one('product.template', string='Product template', ondelete='cascade')
    image = fields.Image()
    url = fields.Char(string="Image URL", help="External URL of image")

    @api.onchange('url')
    def validate_img_url(self):
        if self.url:
            try:
                image_types = ["image/jpeg", "image/png", "image/tiff",
                               "image/vnd.microsoft.icon", "image/x-icon",
                               "image/vnd.djvu", "image/svg+xml", "image/gif"]
                response = urllib.request.urlretrieve(self.url)

                if response[1].get_content_type() not in image_types:
                    raise UserError(_("Please provide valid Image URL with any extenssion."))
                else:
                    photo = base64.encodebytes(urlopen(self.url).read())
                    self.image = photo

            except Exception as error:
                raise UserError(_("Invalid Url"))


class ProductProduct(models.Model):
    _inherit = 'product.product'

    woo_id = fields.Char('WooCommerce ID')
    woo_regular_price = fields.Float('WooCommerce Regular Price')

    # woo_product_weight = fields.Float("Weight")
    # woo_product_length = fields.Float("Length")
    # woo_product_width = fields.Float("Width")
    # woo_product_height = fields.Float("Height")
    # woo_weight_unit = fields.Char(default="kg")
    # woo_unit_other = fields.Char(default="cm")
    is_exported = fields.Boolean('Synced In Woocommerce', default=False)
    woo_instance_id = fields.Many2one('woo.instance', ondelete='cascade')
    woo_varient_description = fields.Text('Woo Variant Description')
    default_code = fields.Char('Internal Reference', index=True, required=False)
    woo_sale_price = fields.Float('WooCommerce Sales Price')

    def export_selected_product_variant(self, instance_id):
        location = instance_id.url
        cons_key = instance_id.client_id
        sec_key = instance_id.client_secret
        version = 'wc/v3'

        wcapi = API(url=location, consumer_key=cons_key, consumer_secret=sec_key, version=version)

        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['product.product'].sudo().browse(selected_ids)
        all_records = self.env['product.product'].sudo().search([])
        if selected_records:
            records = selected_records
        else:
            records = all_records

        list = []
        for rec in records:
            attributes_lst = []

            if rec.product_tmpl_id.woo_id and rec.product_template_attribute_value_ids:
                for combinations in rec.product_template_attribute_value_ids:
                    dict_attr = {}
                    dict_attr['id'] = combinations.attribute_id.woo_id
                    dict_attr['name'] = combinations.attribute_id.name
                    dict_attr['option'] = combinations.name
                    attributes_lst.append(dict_attr)

            list.append({
                "id": rec.woo_id if rec.woo_id else '',
                "name": rec.product_tmpl_id.woo_id,
                "sku": rec.default_code if rec.default_code else '',
                "regular_price": str(rec.woo_regular_price) if rec.woo_regular_price else '',
                "sale_price": str(rec.woo_sale_price),
                "manage_stock": True,
                "stock_quantity": rec.qty_available,
                "description": str(rec.woo_varient_description) if rec.woo_varient_description else '',
                "weight": str(rec.woo_product_weight) if rec.woo_product_weight else '',
                "dimensions":
                    {
                        "length": str(rec.woo_product_length) if rec.woo_product_length else '',
                        "width": str(rec.woo_product_width) if rec.woo_product_width else '',
                        "height": str(rec.woo_product_height) if rec.woo_product_height else '',
                    },
                "attributes": attributes_lst,
            })

        if list:
            for data in list:
                if data.get('id'):
                    try:
                        parsed_data = wcapi.post("products/%s/variations/%s" % (data.get('name'), data.get('id')), data)
                        if parsed_data.status_code != 200:
                            message = parsed_data.json().get('message')
                            self.env['bus.bus']._sendone(self.env.user.partner_id, 'snailmail_invalid_address', {
                                'title': _("Failed"),
                                'message': _(message),
                            })
                    except Exception as error:
                        raise UserError(_("Please check your connection and try again"))

                else:
                    try:
                        data.pop('id')
                        parsed_data = wcapi.post("products/%s/variations" % (int(data.get('name'))), data)
                        if parsed_data.status_code != 200:
                            message = parsed_data.json().get('message')
                            self.env['bus.bus'].sendone(
                                (self._cr.dbname, 'res.partner', self.env.user.partner_id.id),
                                {'type': 'snailmail_invalid_address', 'title': _("Failed"),
                                 'message': _(message)}
                            )
                    except Exception as error:
                        raise UserError(_("Please check your connection and try again"))

        self.env['product.template'].import_product(instance_id)


class Product(models.Model):
    _inherit = 'product.template'

    woo_id = fields.Char('WooCommerce ID')
    woo_regular_price = fields.Float('WooCommerce Regular Price')
    woo_sale_price = fields.Float('WooCommerce Sale Price')
    commission_type = fields.Selection([
        ('global', 'Global'),
        ('percent', 'Percentage'),
        ('fixed', 'Fixed'),
        ('percent_fixed', 'Percent Fixed'),
    ], "Commission Type")
    commission_value = fields.Float("Commission for Admin")
    fixed_commission_value = fields.Float("Fixed Price")
    woo_product_weight = fields.Float("Woo Weight")
    woo_product_length = fields.Float("Woo Length")
    woo_product_width = fields.Float("Woo Width")
    woo_product_height = fields.Float("Woo Height")
    woo_weight_unit = fields.Char(default="kg")
    woo_unit_other = fields.Char(default="cm")
    website_published = fields.Boolean()
    woo_image_ids = fields.One2many("woo.product.image", "template_id")
    woo_tag_ids = fields.Many2many("product.tag", string="Tags")
    is_exported = fields.Boolean('Synced In Woocommerce', default=False)
    woo_instance_id = fields.Many2one('woo.instance', ondelete='cascade')
    woo_product_qty = fields.Float("Woo Stock Quantity")

    def woo_published(self):
        location = self.woo_instance_id.url
        cons_key = self.woo_instance_id.client_id
        sec_key = self.woo_instance_id.client_secret
        version = 'wc/v3'

        wcapi = API(url=location, consumer_key=cons_key, consumer_secret=sec_key, version=version)
        if self.woo_id:
            try:
                wcapi.post("products/%s" % self.woo_id, {'status': 'publish'}).json()
                self.sudo().write({'website_published': True})
            except Exception as error:
                raise UserError(
                    _("Something went wrong while updating Product.\n\nPlease Check your Connection \n\n" + str(error)))

        return True

    def woo_unpublished(self):
        location = self.woo_instance_id.url
        cons_key = self.woo_instance_id.client_id
        sec_key = self.woo_instance_id.client_secret
        version = 'wc/v3'

        wcapi = API(url=location, consumer_key=cons_key, consumer_secret=sec_key, version=version)
        if self.woo_id:
            try:
                wcapi.post("products/%s" % self.woo_id, {'status': 'draft'}).json()
                self.sudo().write({'website_published': False})
            except Exception as error:
                raise UserError(
                    _("Something went wrong while updating Product.\n\nPlease Check your Connection \n\n" + str(error)))
        return True

    def cron_export_product(self):
        all_instances = self.env['woo.instance'].sudo().search([])
        for rec in all_instances:
            if rec:
                self.env['product.template'].export_selected_product(rec)

    def export_selected_product(self, instance_id):
        location = instance_id.url
        cons_key = instance_id.client_id
        sec_key = instance_id.client_secret
        version = 'wc/v3'

        wcapi = API(url=location, consumer_key=cons_key, consumer_secret=sec_key, version=version)

        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['product.template'].sudo().browse(selected_ids)
        all_records = self.env['product.template'].sudo().search([])
        if selected_records:
            records = selected_records
        else:
            records = all_records

        list = []
        for rec in records:
            attrs = []
            tags_list = []

            if rec.woo_tag_ids:
                for tag in rec.woo_tag_ids:
                    tags_list.append({'name': tag.name})

            if rec.attribute_line_ids:
                for att in rec.attribute_line_ids:
                    if att.attribute_id.woo_id:
                        values = []
                        for val in att.value_ids:
                            values.append(val.name)

                        attrs.append({
                            'id': att.attribute_id.woo_id,
                            'name': att.attribute_id.name,
                            'slug': att.attribute_id.slug,
                            'options': values,
                        })

            images = []
            for img in rec.woo_image_ids:
                images.append({
                    "src": img.url,
                })

            list.append({
                "id": rec.woo_id,
                "name": rec.name,
                "sku": rec.default_code if rec.default_code else '',
                "regular_price": str(rec.woo_regular_price) if rec.woo_regular_price else '',
                "sale_price": str(rec.woo_sale_price),
                "manage_stock": True,
                "stock_quantity": rec.qty_available,
                "description": rec.description if rec.description else '',
                "images": images,
                "categories": [
                    {
                        "id": int(rec.categ_id.woo_id)
                    },
                ],
                "tags": tags_list,
                "purchaseable": rec.purchase_ok,
                "on_sale": rec.sale_ok,
                "weight": str(rec.woo_product_weight) if rec.woo_product_weight else '',
                "dimensions":
                    {
                        "length": str(rec.woo_product_length) if rec.woo_product_length else '',
                        "width": str(rec.woo_product_width) if rec.woo_product_width else '',
                        "height": str(rec.woo_product_height) if rec.woo_product_height else '',
                    },
                "attributes": attrs,
            })

        if list:
            for data in list:
                if data.get('id'):
                    try:
                        print(wcapi.post("products/%s" % (data.get('id')), data).json())
                    except Exception as error:
                        raise UserError(_("Please check your connection and try again"))
                else:
                    try:
                        print(wcapi.post("products", data).json())
                    except Exception as error:
                        raise UserError(_("Please check your connection and try again"))

        self.import_product(instance_id)

    def cron_import_product(self):
        all_instances = self.env['woo.instance'].sudo().search([])
        for rec in all_instances:
            if rec:
                self.env['product.template'].import_product(rec)

    def import_product(self, instance_id):
        page = 1
        while page > 0:
            location = instance_id.url
            cons_key = instance_id.client_id
            sec_key = instance_id.client_secret
            version = 'wc/v3'

            wcapi = API(url=location,
                        consumer_key=cons_key,
                        consumer_secret=sec_key,
                        version=version,
                        timeout=900
                        )

            url = "products"
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
                        ''' This will avoid duplications of products already having woo_id. '''
                        pro_t = []
                        if ele.get('sku'):
                            product = self.env['product.template'].sudo().search(
                                ['|', ('woo_id', '=', ele.get('id')), ('default_code', '=', ele.get('sku'))], limit=1)
                        else:
                            product = self.env['product.template'].sudo().search([('woo_id', '=', ele.get('id'))],
                                                                                 limit=1)

                        ''' This is used to update woo_id of a product, this
                        will avoid duplication of product while syncing product.
                        '''
                        product_without_woo_id = self.env['product.template'].sudo().search(
                            [('woo_id', '=', False), ('default_code', '=', ele.get('sku'))], limit=1)

                        product_product_without_id = self.env['product.product'].sudo().search(
                            [('product_tmpl_id', '=', product_without_woo_id.id)], limit=1)

                        dict_p = {}
                        dict_p['is_exported'] = True
                        dict_p['woo_instance_id'] = instance_id.id
                        dict_p['company_id'] = instance_id.woo_company_id.id
                        dict_p['woo_id'] = ele.get('id') if ele.get('id') else ''
                        dict_p['type'] = 'product'
                        dict_p['website_published'] = True if ele.get('status') and ele.get('status') == 'publish' else False
                        dict_p['name'] = ele.get('name') if ele.get('name') else ''
                        if ele.get('description'):
                            soup = BeautifulSoup(ele.get('description'), 'html.parser')
                            description_converted_to_text = soup.get_text()
                            dict_p['description_sale'] = description_converted_to_text
                            dict_p['description'] = ele.get('description')
                        if ele.get('sku'):
                            dict_p['default_code'] = ele.get('sku')

                        if ele.get('categories'):
                            categ_name = ele.get('categories')[0].get('name')
                            if categ_name:
                                categ = self.env['product.category'].sudo().search([('name', '=', categ_name)], limit=1)
                                if categ:
                                    dict_p['categ_id'] = categ[0].id

                        if ele.get('price'):
                            dict_p['list_price'] = ele.get('price')
                            dict_p['woo_sale_price'] = ele.get('price')
                            dict_p['woo_regular_price'] = ele.get('price')

                        if ele.get('purchaseable'):
                            if ele.get('purchaseable'):

                                dict_p['purchase_ok'] = True
                            else:
                                dict_p['purchase_ok'] = False

                        if ele.get('on_sale'):
                            if ele.get('on_sale'):

                                dict_p['sale_ok'] = True
                            else:
                                dict_p['sale_ok'] = False

                        if ele.get('images'):
                            url = ele.get('images')[0].get('src')
                            response = requests.get(url)
                            if imghdr.what(None, response.content) != 'webp':
                                image = base64.b64encode(requests.get(url).content)
                                dict_p['image_1920'] = image

                        if ele.get('weight'):
                            dict_p['woo_product_weight'] = float(ele.get('weight'))

                        if ele.get('dimensions'):
                            dict_p['woo_product_length'] = float(ele.get('dimensions').get('length')) if ele.get(
                                'dimensions').get('length') else 0.00
                            dict_p['woo_product_width'] = float(ele.get('dimensions').get('width')) if ele.get(
                                'dimensions').get('width') else 0.00
                            dict_p['woo_product_height'] = float(ele.get('dimensions').get('height')) if ele.get(
                                'dimensions').get('height') else 0.00

                        if ele.get('tags'):
                            for rec in ele.get('tags'):
                                existing_tag = self.env['product.tag'].sudo().search(
                                    ['|', ('woo_id', '=', rec.get('id')), ('name', '=', rec.get('name'))], limit=1)
                                dict_value = {}
                                dict_value['is_exported'] = True
                                dict_value['woo_instance_id'] = instance_id.id
                                if rec.get('name'):
                                    dict_value['name'] = rec.get('name')
                                if rec.get('id'):
                                    dict_value['woo_id'] = rec.get('id')

                                if rec.get('description'):
                                    dict_value['description'] = rec.get('description')

                                if rec.get('slug'):
                                    dict_value['slug'] = rec.get('slug')

                                if not existing_tag:
                                    create_tag_value = self.env['product.tag'].sudo().create(dict_value)
                                    pro_t.append(create_tag_value.id)
                                else:
                                    write_tag_value = existing_tag.sudo().write(dict_value)
                                    pro_t.append(existing_tag.id)

                        if not product and product_without_woo_id:
                            product_without_woo_id.sudo().write(dict_p)
                            if product_product_without_id and not ele.get('variations'):
                                product_product_without_id.sudo().write({
                                    'is_exported': True,
                                    'woo_id': dict_p['woo_id'],
                                    'woo_sale_price': product_without_woo_id.woo_sale_price
                                })

                        if product and not product_without_woo_id:
                            product.sudo().write(dict_p)

                        if not product and not product_without_woo_id:
                            dict_p['type'] = 'product'
                            '''If product is not present we create it'''
                            pro_create = self.env['product.template'].sudo().create(dict_p)
                            product_product_vr = self.env['product.product'].sudo().search(
                                [('product_tmpl_id', '=', pro_create.id)])
                            if product_product_vr and not ele.get('variations'):
                                product_product_vr.sudo().write({
                                    'is_exported': True,
                                    'woo_id': dict_p['woo_id'],
                                    'woo_sale_price': pro_create.woo_sale_price
                                })
                            if pro_t:
                                for val in pro_t:
                                    pro_create.woo_tag_ids = [(4, val)]
                            if pro_create:
                                for rec in ele.get('meta_data'):
                                    if rec.get('key') == '_wcfm_product_author':
                                        vendor_id = rec.get('value')
                                        vendor_odoo_id = self.env['res.partner'].sudo().search(
                                            [('woo_id', '=', vendor_id)], limit=1)
                                        if vendor_odoo_id:
                                            seller = self.env['product.supplierinfo'].sudo().create({
                                                'name': vendor_odoo_id.id,
                                                'product_id': pro_create.id
                                            })
                                            pro_create.seller_ids = [(6, 0, [seller.id])]

                                    if rec.get('key') == '_wcfmmp_commission':
                                        pro_create.commission_type = rec.get('value').get('commission_mode')
                                        if pro_create.commission_type == 'percent':
                                            pro_create.commission_value = rec.get('value').get('commission_percent')
                                        elif pro_create.commission_type == 'fixed':
                                            pro_create.fixed_commission_value = rec.get('value').get(
                                                'commission_fixed')
                                        elif pro_create.commission_type == 'percent_fixed':
                                            pro_create.commission_value = rec.get('value').get('commission_percent')
                                            pro_create.fixed_commission_value = rec.get('value').get(
                                                'commission_fixed')

                                if ele.get('attributes'):
                                    dict_attr = {}
                                    for rec in ele.get('attributes'):
                                        product_attr = self.env['product.attribute'].sudo().search(
                                            ['|', ('woo_id', '=', rec.get('id')), ('name', '=', rec.get('name'))],
                                            limit=1)
                                        dict_attr['is_exported'] = True
                                        dict_attr['woo_instance_id'] = instance_id.id
                                        if rec.get('id'):
                                            dict_attr['woo_id'] = rec.get('id')
                                        if rec.get('name'):
                                            dict_attr['name'] = rec.get('name')
                                        if rec.get('slug'):
                                            dict_attr['slug'] = rec.get('slug')

                                        pro_val = []

                                        if rec.get('options'):
                                            for value in rec.get('options'):
                                                existing_attr_value = self.env['product.attribute.value'].sudo().search(
                                                    [('name', '=', value), ('attribute_id', '=', product_attr.id)],
                                                    limit=1)
                                                dict_value = {}
                                                dict_value['is_exported'] = True
                                                dict_value['woo_instance_id'] = instance_id.id
                                                if value:
                                                    dict_value['name'] = value
                                                    dict_value['attribute_id'] = product_attr.id
                                                if not existing_attr_value and dict_value['attribute_id']:
                                                    create_value = self.env['product.attribute.value'].sudo().create(
                                                        dict_value)
                                                    pro_val.append(create_value.id)

                                                elif existing_attr_value:
                                                    write_value = existing_attr_value.sudo().write(dict_value)
                                                    pro_val.append(existing_attr_value.id)

                                        if product_attr:
                                            if pro_val:
                                                exist = self.env['product.template.attribute.line'].sudo().search(
                                                    [('attribute_id', '=', product_attr.id),
                                                     ('value_ids', 'in', pro_val),
                                                     ('product_tmpl_id', '=', pro_create.id)], limit=1)
                                                if not exist:
                                                    create_attr_line = self.env[
                                                        'product.template.attribute.line'].sudo().create({
                                                        'attribute_id': product_attr.id,
                                                        'value_ids': [(6, 0, pro_val)],
                                                        'product_tmpl_id': pro_create.id
                                                    })
                                                else:
                                                    exist.sudo().write({
                                                        'attribute_id': product_attr.id,
                                                        'value_ids': [(6, 0, pro_val)],
                                                        'product_tmpl_id': pro_create.id
                                                    })

                                if ele.get('variations'):
                                    url = location + '/wp-json/wc/v3'
                                    consumer_key = cons_key
                                    consumer_secret = sec_key
                                    session = requests.Session()
                                    session.auth = (consumer_key, consumer_secret)
                                    product_id = ele.get('id')
                                    endpoint = f"{url}/products/{product_id}/variations"
                                    response = session.get(endpoint)
                                    # var_url = "products/%s/variations" % (ele.get('id'))
                                    # try:
                                    #     data = wcapi.get(var_url, params={'per_page': 100, 'page': page})
                                    # except Exception as error:
                                    #     _logger.error("Something went wrong while fetching variations like:- %s",
                                    #                   error)
                                    if response.status_code == 200 and response.content:
                                        parsed_variants_data = json.loads(response.text)
                                        product_variant = self.env['product.product'].sudo().search(
                                            [('product_tmpl_id', '=', pro_create.id)])

                                        lines_without_no_variants = pro_create.valid_product_template_attribute_line_ids._without_no_variant_attributes()
                                        all_variants = pro_create.with_context(
                                            active_test=False).product_variant_ids.sorted(
                                            lambda p: (p.active, -p.id))
                                        single_value_lines = lines_without_no_variants.filtered(
                                            lambda ptal: len(ptal.product_template_value_ids._only_active()) == 1)

                                        if single_value_lines:
                                            for variant in all_variants:
                                                combination = variant.product_template_attribute_value_ids | single_value_lines.product_template_value_ids._only_active()

                                        all_combinations = itertools.product(
                                            *[ptal.product_template_value_ids._only_active() for ptal in
                                              lines_without_no_variants])

                                        if parsed_variants_data:
                                            for variant in parsed_variants_data:
                                                list_1 = []
                                                for var in variant.get('attributes'):
                                                    list_1.append(var.get('option'))
                                                for item in product_variant:
                                                    if item.product_template_attribute_value_ids:
                                                        list_values = []
                                                        for rec in item.product_template_attribute_value_ids:
                                                            list_values.append(rec.name)

                                                        if set(list_1).issubset(list_values):
                                                            item.default_code = variant.get('sku')
                                                            item.woo_sale_price = variant.get('sale_price')
                                                            item.woo_regular_price = variant.get('regular_price')
                                                            item.woo_id = variant.get('id')
                                                            item.woo_instance_id = instance_id
                                                            item.qty_available = variant.get('stock_quantity')
                                                            item.woo_product_weight = variant.get('weight')
                                                            item.is_exported = True

                                                            if variant.get('dimensions'):
                                                                if variant.get('dimensions').get('length'):
                                                                    item.woo_product_length = variant.get(
                                                                        'dimensions').get(
                                                                        'length')
                                                                if variant.get('dimensions').get('width'):
                                                                    item.woo_product_width = variant.get(
                                                                        'dimensions').get(
                                                                        'width')
                                                                if variant.get('dimensions').get('height'):
                                                                    item.woo_product_height = variant.get(
                                                                        'dimensions').get(
                                                                        'height')

                                                            if variant.get('description'):
                                                                item.woo_varient_description = variant.get(
                                                                    'description').replace(
                                                                    '<p>', '').replace('</p>', '')

                                            for combination_tuple in all_combinations:
                                                combination = self.env['product.template.attribute.value'].concat(
                                                    *combination_tuple)
                                                list_var = []
                                                for n in combination:
                                                    list_var.append(n.name)

                                pro_create.default_code = ele.get('sku')
                            self.env.cr.commit()

                        else:
                            pro_create = product.sudo().write(dict_p)

                            product_product = self.env['product.product'].sudo().search(
                                [('product_tmpl_id', '=', product.id)], limit=1)
                            if product_product and not ele.get('variations'):
                                product_product.sudo().write({
                                    'is_exported': True,
                                    'woo_id': dict_p['woo_id'],
                                    'woo_sale_price': product.woo_sale_price
                                })
                            if pro_t:
                                for val in pro_t:
                                    product.woo_tag_ids = [(4, val)]

                            if ele.get('attributes'):
                                dict_attr = {}

                                for rec in ele.get('attributes'):
                                    product_attr = self.env['product.attribute'].sudo().search(
                                        ['|', ('woo_id', '=', rec.get('id')), ('name', '=', rec.get('name'))], limit=1)
                                    dict_attr['is_exported'] = True
                                    dict_attr['woo_instance_id'] = instance_id.id
                                    if rec.get('id'):
                                        dict_attr['woo_id'] = rec.get('id')
                                    if rec.get('name'):
                                        dict_attr['name'] = rec.get('name')
                                    if rec.get('slug'):
                                        dict_attr['slug'] = rec.get('slug')

                                    pro_val = []

                                    if rec.get('options'):
                                        for value in rec.get('options'):
                                            existing_attr_value = self.env['product.attribute.value'].sudo().search(
                                                [('name', '=', value), ('attribute_id', '=', product_attr.id)], limit=1)
                                            dict_value = {}
                                            dict_value['is_exported'] = True
                                            dict_value['woo_instance_id'] = instance_id.id
                                            if value:
                                                dict_value['name'] = value
                                                dict_value['attribute_id'] = product_attr.id

                                            if not existing_attr_value and dict_value['attribute_id']:
                                                create_value = self.env['product.attribute.value'].sudo().create(
                                                    dict_value)
                                                pro_val.append(create_value.id)

                                            elif existing_attr_value:
                                                write_value = existing_attr_value.sudo().write(dict_value)
                                                pro_val.append(existing_attr_value.id)

                                    if product_attr:
                                        if pro_val:
                                            exist = self.env['product.template.attribute.line'].sudo().search(
                                                [('attribute_id', '=', product_attr.id),
                                                 ('value_ids', 'in', pro_val),
                                                 ('product_tmpl_id', '=', product.id)], limit=1)
                                            if not exist:
                                                create_attr_line = self.env[
                                                    'product.template.attribute.line'].sudo().create({
                                                    'attribute_id': product_attr.id,
                                                    'value_ids': [(6, 0, pro_val)],
                                                    'product_tmpl_id': product.id
                                                })
                                            else:
                                                exist.sudo().write({
                                                    'attribute_id': product_attr.id,
                                                    'value_ids': [(6, 0, pro_val)],
                                                    'product_tmpl_id': product.id
                                                })

                            if ele.get('variations'):
                                url = location + '/wp-json/wc/v3'
                                consumer_key = cons_key
                                consumer_secret = sec_key
                                session = requests.Session()
                                session.auth = (consumer_key, consumer_secret)
                                product_id = ele.get('id')
                                endpoint = f"{url}/products/{product_id}/variations"
                                response = session.get(endpoint)
                                # var_url = "products/%s/variations" % (ele.get('id'))
                                # try:
                                #     data = wcapi.get(var_url, params={'per_page': 100, 'page': page})
                                # except Exception as error:
                                #     _logger.error("Something went wrong while fetching variations like:- %s", error)

                                if response.status_code == 200 and response.content:
                                    parsed_variants_data = json.loads(response.text)
                                    variant_list = []
                                    product_variant = self.env['product.product'].sudo().search(
                                        [('product_tmpl_id', '=', product.id)])

                                    lines_without_no_variants = product.valid_product_template_attribute_line_ids._without_no_variant_attributes()
                                    all_variants = product.with_context(
                                        active_test=False).product_variant_ids.sorted(
                                        lambda p: (p.active, -p.id))
                                    single_value_lines = lines_without_no_variants.filtered(
                                        lambda ptal: len(ptal.product_template_value_ids._only_active()) == 1)

                                    if single_value_lines:
                                        for variant in all_variants:
                                            combination = variant.product_template_attribute_value_ids | single_value_lines.product_template_value_ids._only_active()

                                    all_combinations = itertools.product(
                                        *[ptal.product_template_value_ids._only_active() for ptal in
                                          lines_without_no_variants])

                                    if parsed_variants_data:
                                        for variant in parsed_variants_data:
                                            list_1 = []
                                            for var in variant.get('attributes'):
                                                list_1.append(var.get('option'))
                                            for item in product_variant:
                                                if item.product_template_attribute_value_ids:
                                                    list_values = []
                                                    for rec in item.product_template_attribute_value_ids:
                                                        list_values.append(rec.name)

                                                    if set(list_1).issubset(list_values):
                                                        item.default_code = variant.get('sku')
                                                        item.woo_sale_price = variant.get('sale_price')
                                                        item.woo_regular_price = variant.get('regular_price')
                                                        item.woo_id = variant.get('id')
                                                        item.woo_instance_id = instance_id
                                                        item.qty_available = variant.get('stock_quantity')
                                                        item.woo_product_weight = variant.get('weight')
                                                        item.is_exported = True

                                                        if variant.get('dimensions'):
                                                            if variant.get('dimensions').get('length'):
                                                                item.woo_product_length = variant.get(
                                                                    'dimensions').get(
                                                                    'length')
                                                            if variant.get('dimensions').get('width'):
                                                                item.woo_product_width = variant.get(
                                                                    'dimensions').get(
                                                                    'width')
                                                            if variant.get('dimensions').get('height'):
                                                                item.woo_product_height = variant.get(
                                                                    'dimensions').get(
                                                                    'height')

                                                        if variant.get('description'):
                                                            item.woo_varient_description = variant.get(
                                                                'description').replace(
                                                                '<p>', '').replace('</p>', '')

                                        for combination_tuple in all_combinations:
                                            combination = self.env['product.template.attribute.value'].concat(
                                                *combination_tuple)
                                            list_var = []
                                            for n in combination:
                                                list_var.append(n.name)

                            product.default_code = ele.get('sku')

                            for rec in ele.get('meta_data'):
                                if rec.get('key') == '_wcfm_product_author':
                                    vendor_id = rec.get('value')
                                    vendor_odoo_id = self.env['res.partner'].sudo().search([('woo_id', '=', vendor_id)],
                                                                                           limit=1)
                                    if vendor_odoo_id:
                                        vendor_supplier_info = self.env['product.supplierinfo'].sudo().search(
                                            [('name', '=', vendor_odoo_id.id), ('product_id', '=', product.id)],
                                            limit=1)
                                        if not vendor_supplier_info:
                                            seller = self.env['product.supplierinfo'].sudo().create({
                                                'name': vendor_odoo_id.id,
                                                'product_id': product.id
                                            })
                                            product.seller_ids = [(6, 0, [seller.id])]

                                if rec.get('key') == '_wcfmmp_commission':
                                    product.commission_type = rec.get('value').get('commission_mode')
                                    if product.commission_type == 'percent':
                                        product.commission_value = rec.get('value').get('commission_percent')
                                    elif product.commission_type == 'fixed':
                                        product.fixed_commission_value = rec.get('value').get('commission_fixed')
                                    elif product.commission_type == 'percent_fixed':
                                        product.commission_value = rec.get('value').get('commission_percent')
                                        product.fixed_commission_value = rec.get('value').get('commission_fixed')
                            self.env.cr.commit()
            else:
                page = 0

    def import_inventory(self, instance_id):
        page = 1
        while page > 0:
            location = instance_id.url
            cons_key = instance_id.client_id
            sec_key = instance_id.client_secret
            version = 'wc/v3'

            wcapi = API(url=location,
                        consumer_key=cons_key,
                        consumer_secret=sec_key,
                        version=version,
                        timeout=900
                        )
            url = "products"
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
                        # For products with variants in odoo
                        product = self.env['product.product'].sudo().search(
                            ['|', ('woo_id', '=', ele.get('id')), ('default_code', '=', ele.get('sku'))], limit=1)
                        if product:
                            if ele.get('stock_quantity') and ele.get('stock_quantity') > 0:
                                res_product_qty = self.env['stock.change.product.qty'].sudo().search(
                                    [('product_id', '=', product.id)], limit=1)
                                dict_q = {}
                                dict_q['new_quantity'] = ele.get('stock_quantity')
                                dict_q['product_id'] = product.id
                                dict_q['product_tmpl_id'] = product.product_tmpl_id.id

                                if not res_product_qty:
                                    create_qty = self.env['stock.change.product.qty'].sudo().create(dict_q)
                                    create_qty.change_product_qty()
                                else:
                                    write_qty = res_product_qty.write(dict_q)
                                    qty_id = self.env['stock.change.product.qty'].sudo().search(
                                        [('product_id', '=', product.id)], limit=1)
                                    if qty_id:
                                        qty_id.change_product_qty()

                        # For products without variants
                        product = self.env['product.template'].sudo().search(
                            ['|', ('woo_id', '=', ele.get('id')), ('default_code', '=', ele.get('sku'))], limit=1)
                        if product:
                            url = location + '/wp-json/wc/v3'
                            consumer_key = cons_key
                            consumer_secret = sec_key
                            session = requests.Session()
                            session.auth = (consumer_key, consumer_secret)
                            product_id = product.woo_id
                            endpoint = f"{url}/products/{product_id}/variations"
                            response = session.get(endpoint)
                            if response.status_code == 200:
                                parsed_variants_data = json.loads(response.text)
                                for ele in parsed_variants_data:
                                    if ele.get('stock_quantity') and ele.get('stock_quantity') > 0:
                                        product_p = self.env['product.product'].sudo().search(
                                            ['|', ('woo_id', '=', ele.get('id')),
                                             ('default_code', '=', ele.get('sku'))], limit=1)
                                        if product_p:
                                            res_product_qty = self.env['stock.change.product.qty'].sudo().search(
                                                [('product_id', '=', product_p.id)], limit=1)
                                            dict_q = {}
                                            dict_q['new_quantity'] = ele.get('stock_quantity')
                                            dict_q['product_id'] = product_p.id
                                            dict_q['product_tmpl_id'] = product_p.product_tmpl_id.id

                                            if not res_product_qty:
                                                create_qty = self.env['stock.change.product.qty'].sudo().create(dict_q)
                                                create_qty.change_product_qty()
                                            else:
                                                write_qty = res_product_qty.sudo().write(dict_q)
                                                qty_id = self.env['stock.change.product.qty'].sudo().search(
                                                    [('product_id', '=', product_p.id)], limit=1)
                                                if qty_id:
                                                    qty_id.change_product_qty()

                            product.woo_product_qty = ele.get('stock_quantity') if ele.get(
                                'stock_quantity') and ele.get('stock_quantity') > 0 else 0.00
            else:
                page = 0