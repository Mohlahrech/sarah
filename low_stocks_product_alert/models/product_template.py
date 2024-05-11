# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'product template'
    
    alert_state = fields.Boolean(string='Product Alert State', default=False,
                                 compute='_compute_alert_state')
    color_field = fields.Char(string='Background color')
    stock_min = fields.Integer(string='Stock Minimal', default='0')
    
    quantity_check = quantity_check = fields.Selection([('global', 'Global'), ('individuel', 'Par Produit')], string="Quantité produit minimal", default='global')

    @api.depends('qty_available')
    def _compute_alert_state(self):
        is_low_stock_alert = self.env[
            'ir.config_parameter'].sudo().get_param(
            'low_stocks_product_alert.is_low_stock_alert')
        min_low_stock_alert = self.env[
            'ir.config_parameter'].sudo().get_param(
            'low_stocks_product_alert.min_low_stock_alert')
        quantity_check = self.env[
            'ir.config_parameter'].sudo().get_param(
            'low_stocks_product_alert.quantity_check'
            )
        if is_low_stock_alert:
            if quantity_check == 'global':
                for rec in self:
                    rec.alert_state = False
                    rec.color_field = 'white'
                    if rec.detailed_type == 'product':
                        if rec.qty_available <= int(min_low_stock_alert):
                            rec.alert_state = True
                            rec.color_field = '#fdc6c673'
            elif quantity_check == 'individuel':
                for rec in self:
                    rec.alert_state = False
                    rec.color_field = 'white'
                    if rec.detailed_type == 'product':
                        if rec.qty_available <= int(rec.stock_min):
                            rec.alert_state = True
                            rec.color_field = '#fdc6c673'
                
        else:
            self.alert_state = False
            self.color_field = 'white'

