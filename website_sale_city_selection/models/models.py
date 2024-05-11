# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CountryState(models.Model):
    _inherit = "res.country.state"

    city_ids = fields.One2many('res.city', 'state_id')

    def get_website_sale_city(self, mode='billing'):
        return self.sudo().city_ids


