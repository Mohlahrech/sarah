# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    group_stock_alert = fields.Boolean("Stock", implied_group='low_stocks_product_alert.group_stock_alert')
    is_low_stock_alert = fields.Boolean(string="Low Stock Alert")
    quantity_check = fields.Selection([('global', 'Global'), ('individuel', 'Par Produit')], string="Quantité produit minimal", default='global')
    min_low_stock_alert = fields.Integer(
        string='Quantite Seuil', default=0,
        help='Change the background color for the product based'
             ' on the Alert Quant.')
             
    def set_values(self):
        super(ResConfig, self).set_values()

        self.env['ir.config_parameter'].set_param(
            'low_stocks_product_alert.is_low_stock_alert', self.is_low_stock_alert)

        self.env['ir.config_parameter'].set_param(
            'low_stocks_product_alert.min_low_stock_alert', self.min_low_stock_alert)
        
        self.env['ir.config_parameter'].set_param(
            'low_stocks_product_alert.quantity_check', self.quantity_check)
        
    @api.onchange('quantity_check')
    def _onchange_quantity_check(self):
        if self.quantity_check =='individuel':
            self.write({'group_stock_alert': True})
        else :
            self.write({'group_stock_alert': False})
            
            
    @api.model 
    def get_values(self):
        res = super(ResConfig, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            is_low_stock_alert=params.get_param(
                'low_stocks_product_alert.is_low_stock_alert'),
            min_low_stock_alert=params.get_param(
                'low_stocks_product_alert.min_low_stock_alert'),
            quantity_check=params.get_param(
                'low_stocks_product_alert.quantity_check'),
        )
        return res
