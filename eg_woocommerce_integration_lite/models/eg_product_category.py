import logging

from odoo import fields, models

_logging = logging.getLogger("===+++ eCom Product Category +++===")


class EgProductCategory(models.Model):
    _inherit = 'eg.product.category'

    slug = fields.Char(string="Slug")
    description = fields.Text(string="Description")
    display = fields.Selection(
        [('default', 'Default'), ('products', 'Products'), ('subcategories', 'Subcategories'), ('both', 'Both')])
    menu_order = fields.Integer(string="Menu order")
    count = fields.Integer(string="Count")
    image_src = fields.Char(string="Image Src")
