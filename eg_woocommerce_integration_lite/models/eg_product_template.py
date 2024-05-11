import logging

from odoo import models, fields

_logger = logging.getLogger("===+++ eCOm Product Template +++===")


class EgProductTemplate(models.Model):
    _inherit = 'eg.product.template'

    no_export_woo = fields.Boolean(string='No Export WC')
    is_woocommerce_tmpl_product = fields.Boolean(string='Available in WC')
    product_price = fields.Float(string='Product Price')

    regular_price = fields.Float(string='Regular Price')
    sale_ok = fields.Boolean(string="Product Sold")
    purchase_ok = fields.Boolean("Can be Purchased")

    date_on_sale_from = fields.Char(string="Sale start date")
    date_on_sale_to = fields.Char(string="Sale end date")

    slug = fields.Char(string="Slug")
    permalink = fields.Char(string='Permalink')
    woo_product_tmpl_type = fields.Selection(
        [('simple', 'Simple'), ('grouped', 'Grouped'), ('external', 'External'), ('variable', 'Variable')],
        string="Product Type")
    status = fields.Selection(
        [("draft", "Draft"), ("pending", "Pending"), ("private", "Private"), ("publish", "Publish")])
    catalog_visibility = fields.Selection(
        [("visible", "Visible"), ("catalog", "Catalog"), ("search", "Search"), ("hidden", "Hidden")])
    virtual = fields.Boolean(string='Virtual')
    external_url = fields.Char(string='External Url')
    button_text = fields.Char(string='Button Text')
    tax_status = fields.Selection([('taxable', 'Taxable'), ('shipping', 'Shipping'), ('none', 'None')])
    tax_class = fields.Char(string='Tax Class')

    manage_stock = fields.Boolean(string='Manage Stock')
    stock_status = fields.Selection(
        [("instock", "Instock"), ("outofstock", "Outofstock"), ("onbackorder", "Onbackorder")])

    backorders = fields.Selection([("no", "No"), ("notify", "Notify"), ("yes", "Yes")])
    backorders_allowed = fields.Boolean(string='BackOrder Allowed')
    backordered = fields.Boolean(string='Backordered')
    sold_individually = fields.Boolean(string='Sold Individually')

    shipping_required = fields.Boolean(string='Shipping Required')
    shipping_taxable = fields.Boolean(string='Shipping Taxable')
    shipping_class = fields.Char(string='Shipping Class')
    shipping_class_id = fields.Integer(string='Shipping class id')

    reviews_allowed = fields.Boolean(string='Reviews Allowed')
    average_rating = fields.Float(string='Average Rating')
    rating_count = fields.Integer(string='Rating Count')
    product_tmpl_length = fields.Float(string='Length')
    product_tmpl_width = fields.Float(string='Width')
    product_tmpl_height = fields.Float(string='Height')
    need_to_update = fields.Boolean(string='Need To Update')

    product_attribute_ids = fields.One2many(comodel_name='eg.product.attribute', inverse_name='eg_product_tmpl_id')

    woo_product_tmpl_image_src = fields.Char(string='Image Src')

    def export_product_odoo_to_ecom(self):
        for rec in self:
            if rec.instance_id.provider == "eg_woocommerce":
                rec.woo_odoo_product_template_export()
        return super(EgProductTemplate, self).export_product_odoo_to_ecom()

    def check_product_sku(self, woo_tmpl_dict):
        _logger.info("{} not set a Sku".format(woo_tmpl_dict.get('name')))

    def create_product_attributes(self, woo_tmpl_dict, woo_api):
        """
        In this create attribute and his value in odoo and middle layer from woocommerce 
        :param woo_tmpl_dict: dict of product template data
        :param woo_api: Browseable object of instance
        :return: Nothing
        """
        #  Change code flow and solve some issue by Akash
        product_attribute_obj = self.env['product.attribute']
        product_attribute_value_obj = self.env['product.attribute.value']
        woo_product_attribute_obj = self.env['eg.product.attribute']
        woo_attribute_terms_obj = self.env['eg.attribute.value']
        for attribute_dict in woo_tmpl_dict.get('attributes'):
            odoo_attribute_id = self.env['product.attribute'].search(
                [('name', '=', attribute_dict.get('name'))])
            eg_attribute_id = self.env['eg.product.attribute'].search(
                [('inst_attribute_id', '=', str(attribute_dict.get('id'))), ('instance_id', '=', woo_api.id)])
            if not odoo_attribute_id:
                odoo_attribute_id = product_attribute_obj.create({'name': attribute_dict.get('name')})
                for attribute_value in attribute_dict.get('options'):
                    product_attribute_value_obj.create({'name': attribute_value,
                                                        'attribute_id': odoo_attribute_id.id, })
            else:
                for attribute_value in attribute_dict.get('options'):
                    odoo_attribute_value_id = self.env['product.attribute.value'].search(
                        [('attribute_id', '=', odoo_attribute_id.id), ('name', '=', attribute_value)])
                    if not odoo_attribute_value_id:
                        product_attribute_value_obj.create({'attribute_id': odoo_attribute_id.id,
                                                            'name': attribute_value, })

            if not eg_attribute_id:
                eg_attribute_id = woo_product_attribute_obj.create({'instance_id': woo_api.id,
                                                                    'name': attribute_dict.get('name'),
                                                                    'odoo_attribute_id': odoo_attribute_id.id,
                                                                    'inst_attribute_id': str(
                                                                        attribute_dict.get('id')), })
                for attribute_value in attribute_dict.get('options'):
                    product_attribute_value_id = self.env['product.attribute.value'].search(
                        [('name', '=', attribute_value), ("attribute_id", "=", odoo_attribute_id.id)])
                    woo_attribute_terms_obj.create({'instance_id': woo_api.id,
                                                    'name': attribute_value,
                                                    'inst_attribute_id': eg_attribute_id.id,
                                                    'odoo_attribute_value_id': product_attribute_value_id.id, })
            else:
                for attribute_value in attribute_dict.get('options'):
                    woo_attribute_terms_id = self.env['eg.attribute.value'].search(
                        [('inst_attribute_id', '=', eg_attribute_id.id),
                         ('name', '=', attribute_value), ('instance_id', '=', woo_api.id)])
                    if not woo_attribute_terms_id:
                        product_attribute_value_id = self.env['product.attribute.value'].search(
                            [('name', '=', attribute_value), ("attribute_id", "=", odoo_attribute_id.id)])
                        woo_attribute_terms_obj.create({'instance_id': woo_api.id,
                                                        'inst_attribute_id': eg_attribute_id.id,
                                                        'name': attribute_value,
                                                        'odoo_attribute_value_id': product_attribute_value_id.id, })

    def set_odoo_product_attribute(self, woo_tmpl_dict, woo_api):
        """
        In this find and make list of odoo attribute and and his value for attribute line in odoo product.
        :param woo_tmpl_dict: dict of product template data
        :param woo_api: Browseable object of instance
        :return: list of odoo attribute line data
        """
        line_value_list = []
        for product_attribute in woo_tmpl_dict.get("attributes"):
            product_attribute_value_ids = self.env['product.attribute.value']
            eg_attribute_id = self.env['eg.product.attribute'].search(
                [('inst_attribute_id', '=', str(product_attribute.get('id'))), ('instance_id', '=', woo_api.id)])
            for product_attribute_option in product_attribute.get('options'):
                for value_id in eg_attribute_id.odoo_attribute_id.value_ids:
                    if product_attribute_option == value_id.name:
                        product_attribute_value_ids += value_id
            print(product_attribute_value_ids)
            line_value_list.append(
                (0, False, {'attribute_id': eg_attribute_id.odoo_attribute_id.id,
                            'value_ids': [(6, 0, product_attribute_value_ids.ids)]}))
        return line_value_list

    def set_woo_product_attribute(self, woo_tmpl_dict, woo_api):
        """
        In this find and make list of mapping attribute and and his value for attribute line in mapping product
        :param woo_tmpl_dict: dict of product template data
        :param woo_api: Browseable object of instance
        :return: list of mapping attribute line data
        """
        woo_line_value_list = []
        for product_attribute in woo_tmpl_dict.get("attributes"):
            eg_value_ids = self.env['eg.attribute.value']
            eg_attribute_id = self.env['eg.product.attribute'].search(
                [('inst_attribute_id', '=', str(product_attribute.get('id'))), ('instance_id', '=', woo_api.id)])
            for product_attribute_option in product_attribute.get('options'):
                for value_id in eg_attribute_id.eg_value_ids:
                    if product_attribute_option == value_id.name:
                        eg_value_ids += value_id
            woo_line_value_list.append(
                (0, False, {'eg_product_attribute_id': eg_attribute_id.id,
                            'eg_value_ids': [(6, 0, eg_value_ids.ids)]}))
        return woo_line_value_list

    def import_product_template(self, instance_id, product_tmpl_dict=None, eg_product_id=None):
        """
         In this method create odoo product with category, attribute, attribute value, and set image to middle layer 
          and create record of mapping product and if product is already mapped so check any new variant add so 
          add variant in odoo and middle layer, if odoo product is available but not in mappping so compare attribute a
          nd value if sem so mapping product else not mapped.
        :param instance_id: Browseable object of instance
        :param product_tmpl_dict: Dict of product template data
        :param eg_product_id: id of woocommerce product
        :return: Nothing
        """
        status = "no"
        text = ""
        partial = False
        history_id_list = []
        woo_api = instance_id
        page = 1
        try:
            wcapi = woo_api.get_wcapi_connection()
        except Exception as e:
            raise Warning("{}".format(e))
        while page > 0:
            if product_tmpl_dict:
                response = wcapi.get("products/{}".format(product_tmpl_dict.get('product_id')))
                page = 0
            elif eg_product_id:
                response = wcapi.get("products/{}".format(eg_product_id))
                page = 0
            else:
                response = wcapi.get('products', params={'per_page': 100, 'page': page})
                page += 1
            if response.status_code == 200:
                if product_tmpl_dict:
                    product_list = [response.json()]
                elif eg_product_id:
                    product_list = [response.json()]
                else:
                    product_list = response.json()
                if not product_list:
                    page = 0
                for woo_tmpl_dict in product_list:  # Changes by Akash
                    status = "no"
                    history_product_id = None
                    if woo_tmpl_dict.get("status") != "trash":
                        eg_product_tmpl_id = self.search(
                            [('inst_product_tmpl_id', '=', str(woo_tmpl_dict.get('id'))),
                             ('instance_id', '=', woo_api.id)])

                        if not eg_product_tmpl_id or eg_product_tmpl_id and not eg_product_tmpl_id.odoo_product_tmpl_id:
                            if woo_tmpl_dict.get('type') == 'variable':
                                if woo_tmpl_dict.get('variations'):
                                    odoo_product_tmpl_id = None
                                    odoo_product_id = None
                                    if woo_tmpl_dict.get('attributes'):

                                        self.create_product_attributes(woo_tmpl_dict, woo_api)
                                    else:
                                        _logger.info(
                                            "This product is not create and not mapped because tpee is variant but not available attribute : {}".format(
                                                woo_tmpl_dict.get("name")))
                                        continue
                                    if woo_tmpl_dict.get("sku"):
                                        odoo_product_tmpl_id = self.env["product.template"].search(
                                            [("default_code", "=", woo_tmpl_dict.get("sku"))])
                                    if not woo_tmpl_dict.get("sku") or not odoo_product_tmpl_id:
                                        product_response = wcapi.get(
                                            "products/{}/variations/{}".format(woo_tmpl_dict.get('id'),
                                                                               woo_tmpl_dict.get('variations')[
                                                                                   0])).json()
                                        odoo_product_id = self.env['product.product'].search(
                                            [('default_code', '=', product_response.get('sku'))])
                                    if not odoo_product_id and not odoo_product_tmpl_id:
                                        odoo_product_tmpl_id = self.env['product.template'].create({
                                            'name': woo_tmpl_dict.get("name"),
                                            'list_price': woo_tmpl_dict.get("sale_price"),
                                            'default_code': woo_tmpl_dict.get("sku"),
                                            'create_date': woo_tmpl_dict.get("date_created"),
                                            'standard_price': woo_tmpl_dict.get("regular_price"),
                                            'sale_ok': woo_tmpl_dict.get("on_sale"),
                                            'purchase_ok': woo_tmpl_dict.get("purchasable"),
                                            'write_date': woo_tmpl_dict.get("date_modified"),
                                            'weight': woo_tmpl_dict.get("weight"),
                                            'sales_count': woo_tmpl_dict.get("total_sales"),
                                            'description': woo_tmpl_dict.get("description"),
                                            'type': 'product',
                                            'attribute_line_ids': self.set_odoo_product_attribute(woo_tmpl_dict,
                                                                                                  woo_api),
                                        })
                                        mapping_product = True
                                    else:  # Changes by Akash
                                        # if odoo product is available so check attribute and his value sam or not
                                        # if not sem so don't mapping product
                                        if not odoo_product_tmpl_id:
                                            odoo_product_tmpl_id = odoo_product_id.product_tmpl_id
                                        check_attribute_value = self.check_product_attribute_import(
                                            odoo_product_tmpl_id=odoo_product_tmpl_id, woo_tmpl_dict=woo_tmpl_dict)
                                        if not check_attribute_value:
                                            _logger.info({
                                                "This product is not mapped because attribute value are different: {}".format(
                                                    woo_tmpl_dict.get("name"))})
                                            partial = True
                                            text = "This product is not mapped because attribute value are different"
                                            history_product_id = odoo_product_tmpl_id
                                            mapping_product = False
                                        else:
                                            mapping_product = True

                                        #  Changes by Akash
                                    if not eg_product_tmpl_id and mapping_product:
                                        eg_product_tmpl_id = self.create([{
                                            'is_woocommerce_tmpl_product': True,
                                            'instance_id': woo_api.id,
                                            'name': woo_tmpl_dict.get("name"),
                                            'product_price': woo_tmpl_dict.get("price"),
                                            'default_code': woo_tmpl_dict.get("sku"),
                                            'inst_product_tmpl_id': str(woo_tmpl_dict.get("id")),
                                            'odoo_product_tmpl_id': odoo_product_tmpl_id.id,

                                            'date_on_sale_from': woo_tmpl_dict.get("date_on_sale_from"),
                                            'date_on_sale_to': woo_tmpl_dict.get("date_on_sale_to"),

                                            'regular_price': woo_tmpl_dict.get("regular_price"),
                                            'price': woo_tmpl_dict.get('sale_price'),

                                            'sale_ok': woo_tmpl_dict.get("on_sale"),
                                            'purchase_ok': woo_tmpl_dict.get("purchasable"),
                                            'sale_count': woo_tmpl_dict.get("total_sales"),

                                            'slug': woo_tmpl_dict.get("slug"),
                                            'permalink': woo_tmpl_dict.get("permalink"),
                                            'status': woo_tmpl_dict.get("status"),
                                            'catalog_visibility': woo_tmpl_dict.get("catalog_visibility"),
                                            'virtual': woo_tmpl_dict.get("virtual"),
                                            'external_url': woo_tmpl_dict.get("external_url"),
                                            'button_text': woo_tmpl_dict.get("button_text"),
                                            'tax_status': woo_tmpl_dict.get("tax_status"),
                                            'tax_class': woo_tmpl_dict.get("tax_class"),
                                            'shipping_required': woo_tmpl_dict.get("shipping_required"),
                                            'shipping_taxable': woo_tmpl_dict.get("shipping_taxable"),
                                            'shipping_class': woo_tmpl_dict.get("shipping_class"),
                                            'shipping_class_id': woo_tmpl_dict.get("shipping_class_id"),
                                            'reviews_allowed': woo_tmpl_dict.get("reviews_allowed"),
                                            'average_rating': woo_tmpl_dict.get("average_rating"),
                                            'rating_count': woo_tmpl_dict.get("rating_count"),
                                            'woo_product_tmpl_type': woo_tmpl_dict.get("type"),

                                            'product_tmpl_length': woo_tmpl_dict.get("dimensions")['length'],
                                            'product_tmpl_height': woo_tmpl_dict.get("dimensions")['height'],
                                            'product_tmpl_width': woo_tmpl_dict.get("dimensions")['width'],
                                            'eg_attribute_line_ids': self.set_woo_product_attribute(woo_tmpl_dict,
                                                                                                    woo_api),
                                        }])

                                        # create it's Variant
                                        woo_product_variants = wcapi.get(
                                            "products/{}/variations".format(woo_tmpl_dict.get("id"))).json()
                                        #  Changes by Akash
                                        variant_mapping = self.create_product_variant_mapping_import(
                                            woo_product_variants=woo_product_variants, woo_api=woo_api,
                                            woo_tmpl_dict=woo_tmpl_dict)
                                        status = "yes"
                                        text = "This product successfully create and mapping"
                                        history_product_id = odoo_product_tmpl_id
                                    else:
                                        partial = True
                                else:
                                    partial = True
                                    text = "This product type is variations but do no have any variation : {}".format(
                                        woo_tmpl_dict.get("name"))

                            elif woo_tmpl_dict.get('type') == 'simple':
                                if not woo_tmpl_dict.get('sku'):
                                    _logger.info(
                                        "{} not a SKU so not created in odoo!!!".format(woo_tmpl_dict.get('name')))
                                    continue
                                odoo_product_tmpl_id = self.env['product.template'].search(
                                    [('default_code', '=', woo_tmpl_dict.get('sku'))])
                                if not odoo_product_tmpl_id:
                                    odoo_product_tmpl_id = self.env['product.template'].create({
                                        'name': woo_tmpl_dict.get("name"),
                                        'list_price': woo_tmpl_dict.get("sale_price"),
                                        'default_code': woo_tmpl_dict.get("sku"),
                                        'create_date': woo_tmpl_dict.get("date_created"),
                                        'standard_price': woo_tmpl_dict.get("regular_price"),
                                        'sale_ok': woo_tmpl_dict.get("on_sale"),
                                        'purchase_ok': woo_tmpl_dict.get("purchasable"),
                                        'write_date': woo_tmpl_dict.get("date_modified"),
                                        'weight': woo_tmpl_dict.get("weight"),
                                        'sales_count': woo_tmpl_dict.get("total_sales"),
                                        'description': woo_tmpl_dict.get("description"),
                                        'type': 'product',
                                    })

                                if not eg_product_tmpl_id:
                                    eg_product_tmpl_id = self.create([{
                                        'is_woocommerce_tmpl_product': True,
                                        'instance_id': woo_api.id,
                                        'name': woo_tmpl_dict.get("name"),
                                        'product_price': woo_tmpl_dict.get("price"),
                                        'default_code': woo_tmpl_dict.get("sku"),
                                        'inst_product_tmpl_id': str(woo_tmpl_dict.get("id")),
                                        'odoo_product_tmpl_id': odoo_product_tmpl_id.id,

                                        'date_on_sale_from': woo_tmpl_dict.get("date_on_sale_from"),
                                        'date_on_sale_to': woo_tmpl_dict.get("date_on_sale_to"),

                                        'regular_price': woo_tmpl_dict.get("regular_price"),
                                        'price': woo_tmpl_dict.get('sale_price'),

                                        'sale_ok': woo_tmpl_dict.get("on_sale"),
                                        'purchase_ok': woo_tmpl_dict.get("purchasable"),
                                        'sale_count': woo_tmpl_dict.get("total_sales"),

                                        'slug': woo_tmpl_dict.get("slug"),
                                        'permalink': woo_tmpl_dict.get("permalink"),
                                        'status': woo_tmpl_dict.get("status"),
                                        'catalog_visibility': woo_tmpl_dict.get("catalog_visibility"),
                                        'virtual': woo_tmpl_dict.get("virtual"),
                                        'external_url': woo_tmpl_dict.get("external_url"),
                                        'button_text': woo_tmpl_dict.get("button_text"),
                                        'tax_status': woo_tmpl_dict.get("tax_status"),
                                        'tax_class': woo_tmpl_dict.get("tax_class"),
                                        'shipping_required': woo_tmpl_dict.get("shipping_required"),
                                        'shipping_taxable': woo_tmpl_dict.get("shipping_taxable"),
                                        'shipping_class': woo_tmpl_dict.get("shipping_class"),
                                        'shipping_class_id': woo_tmpl_dict.get("shipping_class_id"),
                                        'reviews_allowed': woo_tmpl_dict.get("reviews_allowed"),
                                        'average_rating': woo_tmpl_dict.get("average_rating"),
                                        'rating_count': woo_tmpl_dict.get("rating_count"),
                                        'woo_product_tmpl_type': woo_tmpl_dict.get("type"),

                                        'product_tmpl_length': woo_tmpl_dict.get("dimensions")['length'],
                                        'product_tmpl_height': woo_tmpl_dict.get("dimensions")['height'],
                                        'product_tmpl_width': woo_tmpl_dict.get("dimensions")['width'],
                                    }])

                                    product_product_obj = self.env['eg.product.product']
                                    product_product_obj.create({
                                        'is_woocommerce_product': True,
                                        'instance_id': woo_api.id,
                                        'name': woo_tmpl_dict.get("name"),
                                        'inst_product_id': str(woo_tmpl_dict.get("id")),
                                        'odoo_product_id': odoo_product_tmpl_id.product_variant_id.id,
                                        'description': woo_tmpl_dict.get("description"),
                                        'permalink': woo_tmpl_dict.get("permalink"),
                                        'default_code': woo_tmpl_dict.get("sku"),
                                        'product_regular_price': woo_tmpl_dict.get("regular_price"),
                                        'price': woo_tmpl_dict.get("price"),
                                        'on_sale': woo_tmpl_dict.get("on_sale"),
                                        'status': woo_tmpl_dict.get("status"),
                                        'purchasable': woo_tmpl_dict.get("purchasable"),
                                        'virtual': woo_tmpl_dict.get("virtual"),
                                        'date_on_sale_from': woo_tmpl_dict.get("date_on_sale_from"),
                                        'date_on_sale_to': woo_tmpl_dict.get("date_on_sale_to"),
                                        'tax_status': woo_tmpl_dict.get("tax_status"),
                                        'tax_class': woo_tmpl_dict.get("tax_class"),
                                        'weight': woo_tmpl_dict.get("weight"),
                                        'product_length': woo_tmpl_dict.get("dimensions")['length'],
                                        'product_width': woo_tmpl_dict.get("dimensions")['width'],
                                        'product_height': woo_tmpl_dict.get("dimensions")['height'],
                                        'shipping_class': woo_tmpl_dict.get("shipping_class"),
                                        'shipping_class_id': woo_tmpl_dict.get("shipping_class_id"),
                                        'menu_order': woo_tmpl_dict.get("menu_order"),
                                        'eg_tmpl_id': eg_product_tmpl_id.id,
                                    })
                                if odoo_product_tmpl_id:
                                    status = "yes"
                                    text = "This product successfully create and mapping"
                                    history_product_id = odoo_product_tmpl_id
                                else:
                                    partial = True
                        else:  # Changes by Akash
                            # check any new value are add so add in odoo but don't add new attribute
                            if woo_tmpl_dict.get('type') == 'variable':
                                if woo_tmpl_dict.get('attributes'):
                                    self.create_product_attributes(woo_tmpl_dict, woo_api)
                                check_new_variant = self.check_new_product_variant_import(woo_tmpl_dict=woo_tmpl_dict,
                                                                                          eg_product_tmpl_id=eg_product_tmpl_id,
                                                                                          woo_api=woo_api)
                                if check_new_variant:
                                    _logger.info(
                                        "New Variant is add this product : {}".format(woo_tmpl_dict.get("name")))
                                    woo_product_variants = wcapi.get(
                                        "products/{}/variations".format(woo_tmpl_dict.get("id"))).json()
                                    variant_mapping = self.create_product_variant_mapping_import(
                                        woo_product_variants=woo_product_variants, woo_api=woo_api,
                                        woo_tmpl_dict=woo_tmpl_dict)  # Add Pro Version eg_category_ids=eg_category_ids
                                    text = "This product is already mapped but new variant are added"
                                    status = "yes"
                                    history_product_id = eg_product_tmpl_id.odoo_product_tmpl_id
                                else:
                                    continue
                            else:
                                continue
                    else:
                        text = "This product deleted in woocommerce so don't mapped"
                    eg_history_id = self.env["eg.sync.history"].create({"error_message": text,
                                                                        "status": status,
                                                                        "process_on": "product",
                                                                        "process": "a",
                                                                        "instance_id": woo_api.id,
                                                                        "product_id": history_product_id and history_product_id.id or None,
                                                                        "child_id": True})
                    history_id_list.append(eg_history_id.id)

            else:
                text = "Not get a response of a Woocommerce"
            if partial:
                status = "partial"
                text = "Some product was created and some product is not create"
            if status == "yes" and not partial:
                text = "All product was successfully created and mapped"
            if not history_id_list:
                status = "yes"
                text = "All product was already mapped"
            self.env["eg.sync.history"].create({"error_message": text,
                                                "status": status,
                                                "process_on": "product",
                                                "process": "a",
                                                "instance_id": woo_api.id,
                                                "parent_id": True,
                                                "eg_history_ids": [(6, 0, history_id_list)]})

    def check_new_product_variant_import(self, woo_tmpl_dict=None, eg_product_tmpl_id=None,
                                         woo_api=None):  # Changes by Akash (add method)
        """
        In this when import product and any product is already in odoo so check any new variant is add or not , 
        check attribute value not check attribute.
        :param woo_tmpl_dict: dict of product template data
        :param eg_product_tmpl_id: Browseable object of mapping product template
        :param woo_api: Browseable object of instance
        :return: True or False
        """
        variant_mapping = False
        if woo_tmpl_dict.get("attributes"):
            odoo_product_tmpl_id = eg_product_tmpl_id.odoo_product_tmpl_id
            for woo_attribute in woo_tmpl_dict.get("attributes"):
                value_ids = []
                woo_value_ids = []
                attribute_id = self.env["product.attribute"].search([("name", "=", woo_attribute.get("name"))])
                attribute_line_id = odoo_product_tmpl_id.attribute_line_ids.filtered(
                    lambda l: l.attribute_id == attribute_id)
                if attribute_line_id:
                    eg_attribute_id = self.env['eg.product.attribute'].search(
                        [('inst_attribute_id', '=', str(woo_attribute.get('id'))), ('instance_id', '=', woo_api.id)])
                    for woo_value in woo_attribute.get("options"):
                        value_id = self.env["product.attribute.value"].search(
                            [("name", "=", woo_value), ("attribute_id", "=", attribute_id.id)])
                        if value_id not in attribute_line_id.value_ids:
                            woo_value_id = self.env["eg.attribute.value"].search(
                                [('inst_attribute_id', '=', eg_attribute_id.id),
                                 ('name', '=', woo_value), ('instance_id', '=', woo_api.id)])
                            value_ids.append(value_id.id)
                            woo_value_ids.append(woo_value_id.id)
                    if value_ids:
                        variant_mapping = True
                        woo_attribute_line_id = eg_product_tmpl_id.eg_attribute_line_ids.filtered(
                            lambda l: l.eg_product_attribute_id == eg_attribute_id)
                        for value_id in value_ids:
                            attribute_line_id.write({"value_ids": [(4, value_id, 0)]})
                        for woo_value_id in woo_value_ids:
                            woo_attribute_line_id.write({"eg_value_ids": [(4, woo_value_id, 0)]})

        return variant_mapping

    def create_product_variant_mapping_import(self, woo_api=None, woo_product_variants=None,
                                              woo_tmpl_dict=None,
                                              eg_category_ids=None):
        """
         In this method create mapping product variant and write data in odoo product variant.
        :param woo_api: Browseable object of instance
        :param woo_product_variants: lis of dict for product variant data
        :param woo_tmpl_dict: dict of product template data
        :return: True
        """
        for woo_product_dict in woo_product_variants:
            if woo_product_dict.get('sku'):
                woo_product_product_obj = self.env['eg.product.product']
                woo_product_variant_id = self.env['eg.product.product'].search(
                    [('inst_product_id', '=', str(woo_product_dict.get('id'))),
                     ('instance_id', '=', woo_api.id)])
                eg_product_tmpl_id = self.env['eg.product.template'].search(
                    [('inst_product_tmpl_id', '=', str(woo_tmpl_dict.get('id'))),
                     ('instance_id', '=', woo_api.id)])

                if not woo_product_variant_id:
                    attribute_list = []
                    for attribute in woo_product_dict.get('attributes'):
                        eg_attribute_id = self.env['eg.product.attribute'].search(
                            [('inst_attribute_id', '=', str(attribute.get('id'))), ('instance_id', '=', woo_api.id)])
                        woo_attribute_terms = self.env['eg.attribute.value'].search(
                            [('name', '=', attribute.get('option')),
                             ('inst_attribute_id', "=", eg_attribute_id.id), ('instance_id', '=', woo_api.id)])
                        if woo_attribute_terms:
                            attribute_list.append(woo_attribute_terms.id)
                    woo_product_product_id = woo_product_product_obj.create({
                        'is_woocommerce_product': True,
                        'instance_id': woo_api.id,
                        'name': woo_tmpl_dict.get('name'),
                        'inst_product_id': str(woo_product_dict.get('id')),
                        'default_code': woo_product_dict.get('sku'),
                        'eg_tmpl_id': eg_product_tmpl_id.id,
                        'eg_value_ids': [(6, 0, attribute_list)],
                        'product_regular_price': woo_product_dict.get(
                            'regular_price') and float(
                            woo_product_dict.get('regular_price')) or 0.0,
                        'price': woo_product_dict.get('sale_price') and float(
                            woo_product_dict.get('sale_price')) or 0.0,
                        'on_sale': woo_product_dict.get('on_sale'),
                        'purchasable': woo_product_dict.get('purchasable'),
                        'tax_status': woo_product_dict.get('tax_status'),
                        'tax_class': woo_product_dict.get('tax_class'),
                        'shipping_class': woo_product_dict.get('shipping_class'),
                        'shipping_class_id': woo_product_dict.get('shipping_class_id'),
                        'weight': woo_product_dict.get('weight'),
                        'product_length': woo_product_dict.get('dimensions')['length'],
                        'product_width': woo_product_dict.get('dimensions')['width'],
                        'product_height': woo_product_dict.get('dimensions')['height'],
                    })

                    for odoo_product_id in eg_product_tmpl_id.odoo_product_tmpl_id.product_variant_ids:
                        if odoo_product_id.product_template_attribute_value_ids == woo_product_product_id.eg_value_ids.mapped(
                                'odoo_attribute_value_id'):
                            woo_product_product_id.write(
                                {'odoo_product_id': odoo_product_id.id})
                            #  New Change by Akash
                            odoo_product_id.write({
                                'list_price': woo_product_dict.get('sale_price'),
                                'default_code': woo_product_dict.get('sku'),
                                'standard_price': woo_product_dict.get('regular_price'),
                                'sale_ok': woo_product_dict.get("on_sale"),
                                'purchase_ok': woo_product_dict.get("purchasable"),
                                'weight': woo_product_dict.get("weight"),
                                'description': woo_product_dict.get("description"),
                            })
        return True

    def check_product_attribute_import(self, woo_tmpl_dict=None,
                                       odoo_product_tmpl_id=None, ):  # Changes by Akash (add method)
        """
        In this check attribute value of odoo product and woocommerce product sem or not
        :param woo_tmpl_dict: dict of product template data
        :param odoo_product_tmpl_id: Browseable object of odoo product template
        :return: True or False
        """
        if woo_tmpl_dict.get("attributes"):
            for woo_attribute in woo_tmpl_dict.get("attributes"):
                attribute_id = self.env["product.attribute"].search([("name", "=", woo_attribute.get("name"))])
                if attribute_id:
                    attribute_value_ids = self.env["product.attribute.value"].search(
                        [("name", "in", woo_attribute.get("options")), ("attribute_id", "=", attribute_id.id)])
                    compare_values = odoo_product_tmpl_id.attribute_line_ids.filtered(
                        lambda l: l.value_ids == attribute_value_ids)
                    if not compare_values:
                        return False
            return True
        else:
            return False

    def woo_odoo_product_template_export(self, instance_id=None):
        """
        In this create product from middle layer to WooCommerce with mapping product, export category, export attribute value.
        :param instance_id: Browseable object of instance
        :return: Nothing
        """
        status = "no"
        text = ""
        partial = False
        history_id_list = []
        if self:
            eg_product_tmpl_ids = self
        else:
            eg_product_tmpl_ids = self.search([("instance_id", "=", instance_id.id)])
        for record in eg_product_tmpl_ids:
            woo_api = record.instance_id
            try:  # Changes by Akash
                wcapi = woo_api.get_wcapi_connection()
            except Exception as e:
                raise Warning("{}".format(e))
            if not record.is_woocommerce_tmpl_product:
                status = "no"
                eg_product_pricelist_id = self.env['eg.product.pricelist'].search(
                    [('id', '=', woo_api.eg_product_pricelist_id.id)])

                product_price = None
                if eg_product_pricelist_id:
                    for woo_product_pricelist_line in eg_product_pricelist_id.eg_product_pricelist_line_ids:
                        if record.id == woo_product_pricelist_line.eg_product_template_id.id:
                            product_price = woo_product_pricelist_line.price_unit
                            break
                        else:
                            product_price = record.price

                # if product attribute available of current product Template so export a product type of product variable
                attribute_lines = []
                if record.eg_attribute_line_ids:
                    product_type = "variable"  # Changes by Akash
                    sale_price = str(product_price)
                    for product_tmpl_attributes in record.eg_attribute_line_ids:
                        eg_product_attribute_id = product_tmpl_attributes.eg_product_attribute_id
                        option_list = []
                        for prod_attribute_value in product_tmpl_attributes.eg_value_ids:
                            option_list.append(prod_attribute_value.name)
                        if not eg_product_attribute_id.inst_attribute_id:  # add by akash
                            data = {'name': eg_product_attribute_id.name, }
                            woo_attribute_data = wcapi.post("products/attributes", data)
                            if woo_attribute_data.status_code == 201:
                                woo_attribute_data = woo_attribute_data.json()
                            elif woo_attribute_data.status_code == 400:
                                woo_attribute_data = self.env["eg.product.attribute"].import_attribute(
                                    instance_id=woo_api, eg_product_attribute_id=eg_product_attribute_id)
                            eg_product_attribute_id.write({
                                'inst_attribute_id': str(woo_attribute_data.get("id")),
                                'slug': woo_attribute_data.get("slug"),
                                'type': woo_attribute_data.get("type"),
                                'order_by': woo_attribute_data.get("order_by"),
                                'has_archives': woo_attribute_data.get("has_archives"), })
                            for eg_value_id in product_tmpl_attributes.eg_value_ids:
                                value_data = {'name': eg_value_id.name, }
                                woo_term_id = wcapi.post(
                                    "products/attributes/{}/terms".format(
                                        eg_product_attribute_id.inst_attribute_id), value_data)
                                if woo_term_id.status_code == 201:
                                    woo_term_id = woo_term_id.json()
                                    eg_value_id.write({'instance_value_id': woo_term_id.get('id'),
                                                       'slug': woo_term_id.get('slug'),
                                                       'description': woo_term_id.get('description'),
                                                       'menu_order': woo_term_id.get('menu_order'),
                                                       'count': woo_term_id.get('count'), })

                        prod_attribute = {'id': int(eg_product_attribute_id.inst_attribute_id),
                                          'name': product_tmpl_attributes.eg_product_attribute_id.name,
                                          'options': option_list,
                                          'variation': True,
                                          'visible': True, }
                        attribute_lines.append(prod_attribute)

                else:  # Changes by Akash
                    product_type = "simple"
                    sale_price = str(record.price)

                data = {'name': record.name,
                        'type': product_type,
                        'slug': str(record.slug),
                        'permalink': record.permalink,
                        'status': record.status,
                        'catalog_visibility': record.catalog_visibility,
                        'sku': record.default_code and str(record.default_code) or "",
                        'price': str(record.product_price),
                        'regular_price': str(record.regular_price),
                        'sale_price': sale_price,  #
                        'on_sale': record.sale_ok,
                        'purchasable': record.purchase_ok,
                        'total_sales': record.sale_count,
                        'external_url': str(record.external_url),
                        'button_text': str(record.button_text),
                        'tax_status': str(record.tax_status),
                        'tax_class': str(record.tax_class),
                        'shipping_required': record.shipping_required,
                        'shipping_taxable': record.shipping_taxable,
                        'shipping_class': str(record.shipping_class),
                        'shipping_class_id': record.shipping_class_id,
                        'reviews_allowed': record.reviews_allowed,
                        'average_rating': record.average_rating,
                        'rating_count': record.rating_count,
                        'weight': str(record.weight),
                        'attributes': attribute_lines, }

                woo_prod_tmpl = wcapi.post("products", data).json()

                if not woo_prod_tmpl.get("data"):
                    record.write({'inst_product_tmpl_id': str(woo_prod_tmpl.get("id")),
                                  'is_woocommerce_tmpl_product': True,
                                  'update_required': False,
                                  'woo_product_tmpl_type': product_type})
                    if record.eg_attribute_line_ids:
                        # Product template with his variant export to WC
                        record.eg_product_ids.woo_odoo_product_product_export()  # Changes by Akash

                    else:
                        # No required call method  product variant export for without variant product
                        record.eg_product_ids[0].write({"inst_product_id": str(woo_prod_tmpl.get('id')),
                                                        "is_woocommerce_product": True,
                                                        'update_required': False, })  # Changes by Akash
                    status = "yes"
                    text = "This product is successfully export to woocommerce"
                else:
                    partial = True
                    text = "{}".format(woo_prod_tmpl.get("message"))
                    _logger.info(
                        "Export Product Template - ({}) : {}".format(record.name, woo_prod_tmpl.get("message")))
                eg_history_id = self.env["eg.sync.history"].create({"error_message": text,
                                                                    "status": status,
                                                                    "process_on": "product",
                                                                    "process": "b",
                                                                    "instance_id": woo_api.id,
                                                                    "product_id": record.odoo_product_tmpl_id.id,
                                                                    "child_id": True})
                history_id_list.append(eg_history_id.id)
        if partial:
            status = "partial"
            text = "Some product was exported and some product is not exported"
        if status == "yes" and not partial:
            text = "All product was successfully exported in woocommerce"
        if not history_id_list:
            status = "yes"
            text = "All product was already export to woocommerce"
        self.env["eg.sync.history"].create({"error_message": text,
                                            "status": status,
                                            "process_on": "product",
                                            "process": "b",
                                            "instance_id": eg_product_tmpl_ids and eg_product_tmpl_ids[
                                                0].instance_id.id or None,
                                            "parent_id": True,
                                            "eg_history_ids": [(6, 0, history_id_list)]})
