# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    loyalty_points = fields.Float(company_dependent=True, help='The loyalty points the user won as part of a Loyalty Program')

    achats_option = fields.Selection([
        ('magasin', 'Au magasin'),
        ('siteweb', 'Depuis le siteweb'),
        ('Réseaux', 'Via réseaux'),

    ], string='Fait ces achats:')

    barcode2 = fields.Float()
