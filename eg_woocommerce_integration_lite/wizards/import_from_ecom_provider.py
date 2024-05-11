import logging
from odoo import fields, models, api

_logging = logging.getLogger(__name__)


class ImportFromEComProvider(models.TransientModel):
    _inherit = 'import.from.ecom.provider'

    import_woo_tax_rate = fields.Boolean(string="Import Tax Rate",
                                         help="Import Tax Rate from WC to odoo and middle layer")
    import_woo_payment_gateway = fields.Boolean(string="Payment Gateway",
                                                help="Import Payment Gateway from WC to odoo and middle layer")
    import_woo_tax_class = fields.Boolean(string="Tax Class", help="Import Product from WC to odoo and middle layer")
    import_woo_product_coupon = fields.Boolean(string='Product Coupon',
                                               help="Import Tax Class from WC to middle layer")
    export_woo_tax_rate = fields.Boolean(string="Tax Rate", help="Export Tax Rate odoo to WC")
    export_woo_product_coupon = fields.Boolean(string="Product Coupon")

    def import_from_ecom_provider(self):
        if self.provider != "eg_woocommerce":
            return super(ImportFromEComProvider, self).import_from_ecom_provider()
        if self.import_product:
            self.env['eg.product.template'].import_product_template(self.ecom_instance_id)
        if self.import_product_attribute:
            self.env['eg.product.attribute'].import_attribute(self.ecom_instance_id)
        if self.import_product_attribute_value:
            self.env['eg.attribute.value'].import_product_attribute_terms(self.ecom_instance_id)
        if self.import_customer:
            self.env['eg.res.partner'].import_customer(self.ecom_instance_id)
        if self.import_sale_order:
            self.env['eg.sale.order'].import_woo_sale_order(self.ecom_instance_id)
        if self.import_woo_tax_rate:
            self.env['woo.tax.rate'].import_woo_tax_rate(self.ecom_instance_id)
        if self.import_woo_payment_gateway:
            self.env['eg.account.journal'].import_woo_payment_gateway(self.ecom_instance_id)
        if self.import_woo_tax_class:
            self.env['woo.tax.class'].import_woo_tax_class(self.ecom_instance_id)
        if self.import_woo_product_coupon:
            self.env['woo.product.coupon'].import_product_coupon(self.ecom_instance_id)
        if self.export_product:
            self.env['eg.product.template'].woo_odoo_product_template_export(self.ecom_instance_id)
        if self.export_product_attribute:
            self.env['eg.product.attribute'].export_product_attribute(self.ecom_instance_id)
        if self.export_product_attribute_value:
            self.env['eg.attribute.value'].export_woo_product_attribute_terms(self.ecom_instance_id)
        if self.export_woo_tax_rate:
            self.env['woo.tax.rate'].export_tax_rate(self.ecom_instance_id)
        if self.export_woo_product_coupon:
            self.env['woo.product.coupon'].export_product_coupon(self.ecom_instance_id)
