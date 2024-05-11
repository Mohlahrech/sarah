import logging

from odoo import fields, models
from odoo.exceptions import ValidationError

_logging = logging.getLogger("===+++ eCom Product Product +++===")


class EgProductProduct(models.Model):
    _inherit = 'eg.product.product'

    not_export_woo = fields.Boolean(string='No Export WC')
    is_woocommerce_product = fields.Boolean(string='Available in WC')
    description = fields.Text(string="Description")
    permalink = fields.Char(string="Permalink")
    product_regular_price = fields.Float(string="Product Regular Price")
    on_sale = fields.Boolean(string="Can be Sold")
    status = fields.Selection(
        [("draft", "Draft"), ("pending", "Pending"), ("private", "Private"), ("publish", "Publish")], string="Status")
    purchasable = fields.Boolean(string="Can be Purchased")
    virtual = fields.Boolean(string="Virtual")

    date_on_sale_from = fields.Char(string="Sale start date")
    date_on_sale_to = fields.Char(string="Sale end date")

    tax_status = fields.Selection([("taxable", "Taxable"), ("shipping", "Shipping"), ("none", "None")])
    tax_class = fields.Char(string="Tax class")

    manage_stock = fields.Boolean(string="Manage Stock")
    stock_status = fields.Selection(
        [("instock", "In stock"), ("outofstock", "Out of stock"), ("onbackorder", "On BackOrder")])

    backorders = fields.Selection([("no", "No"), ("notify", "Notify"), ("yes", "Yes")])
    backorders_allowed = fields.Boolean(string="Backorder Allowed")
    backordered = fields.Boolean(string="Backordered")

    product_length = fields.Float(string="Length")
    product_width = fields.Float(string="Width")
    product_height = fields.Float(string="Height")

    shipping_class = fields.Char(string="Shipping Class")
    shipping_class_id = fields.Integer(string="Shipping Class ID")
    menu_order = fields.Integer(string="Menu Order")
    woo_product_image_src = fields.Char(string='Image Src')

    def woo_odoo_product_product_export(self):
        """
        In this export product variant middle layer to woocommerce and set woocommerce id in middle layer.
        :return: Nothing
        """
        woo_api = self[0].instance_id
        try:  # Changes by Akash
            wcapi = woo_api.get_wcapi_connection()
        except Exception as e:
            raise Warning("{}".format(e))
        for record in self:
            if not record.is_woocommerce_product:
                if not record.eg_tmpl_id.inst_product_tmpl_id:
                    raise ValidationError("First Import this Variation Product Template")
                else:
                    eg_product_pricelist_id = self.env['eg.product.pricelist'].search(
                        [('id', '=', woo_api.eg_product_pricelist_id.id)])
                    product_price = None
                    if eg_product_pricelist_id:
                        for woo_product_pricelist_line in eg_product_pricelist_id.eg_product_pricelist_line_ids:
                            if record.id == woo_product_pricelist_line.eg_product_id.id:
                                product_price = woo_product_pricelist_line.price_unit
                                break
                            else:
                                product_price = record.price

                    attribute_list = []
                    for attribute_terms_id in record.eg_value_ids:
                        eg_attribute_id = {"id": int(attribute_terms_id.inst_attribute_id.inst_attribute_id),
                                           "option": attribute_terms_id.name,
                                           }
                        attribute_list.append(eg_attribute_id)
                    data = {'sku': record.default_code or "",
                            'regular_price': str(record.product_regular_price),
                            'sale_price': str(product_price),
                            'on_sale': record.on_sale,
                            'purchasable': record.purchasable,
                            'description': record.description and str(record.description) or "",
                            'permalink': record.permalink,
                            'tax_status': record.tax_status,
                            'tax_class': str(record.tax_class),
                            'weight': str(record.weight),
                            "dimensions": {
                                "length": str(record.product_length),
                                "width": str(record.product_width),
                                "height": str(record.product_height),
                            },
                            "shipping_class": str(record.shipping_class),
                            "shipping_class_id": record.shipping_class_id,
                            "attributes": attribute_list,
                            }
                    woo_product_response = wcapi.post(
                        "products/{}/variations".format(record.eg_tmpl_id.inst_product_tmpl_id), data).json()
                    if not woo_product_response.get("data"):  # Changes by Akash
                        record.write({'inst_product_id': str(woo_product_response.get('id')),
                                      'update_required': False,
                                      'is_woocommerce_product': True, })
                    else:
                        _logging.info(
                            "Export Product - ({}) : {}".format(record.name, woo_product_response.get("message")))
            else:
                _logging.info("{} not Export because you check not export in woocommerce".format(record.name))
