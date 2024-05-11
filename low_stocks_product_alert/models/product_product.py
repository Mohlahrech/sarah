# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    alert_tag = fields.Char(
        string='Product Alert State', compute='_compute_alert_tag')
#utilise pour creer popup quand quantite faible dans le  productscreen.js
    stock_min2 = fields.Integer(string='Stock Minimal 2', compute='_compute_stock_min2')

    def _compute_stock_min2(self):
        for product in self:
            product.stock_min2 = product.product_tmpl_id.stock_min
    @api.depends('qty_available')

##
    def _compute_alert_tag(self):
        is_low_stock_alert = self.env[
            'ir.config_parameter'].sudo().get_param(
            'low_stocks_product_alert.is_low_stock_alert')
        min_low_stock_alert = self.env[
            'ir.config_parameter'].sudo().get_param(
            'low_stocks_product_alert.min_low_stock_alert')
        quantity_check = self.env[
            'ir.config_parameter'].sudo().get_param(
            'low_stocks_product_alert.quantity_check')
        if is_low_stock_alert:
            if quantity_check == 'global':
                for rec in self:
                    rec.alert_tag = False
                    if rec.detailed_type == 'product':
                        if rec.qty_available <= int(min_low_stock_alert):
                            rec.alert_tag = rec.qty_available
            elif quantity_check == 'individuel':
                for rec in self:
                    rec.alert_tag = False
                    if rec.detailed_type == 'product':
                        if rec.qty_available <= int(rec.product_tmpl_id.stock_min):
                            rec.alert_tag = rec.qty_available
        else:
            self.alert_tag = False
