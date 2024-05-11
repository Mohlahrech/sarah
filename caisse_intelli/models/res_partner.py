# -*- coding: utf-8 -*-

from odoo import models, fields, api


class partnerfields(models.Model):
    _inherit = 'res.partner'

    barcode = fields.Char(string="Codebar", help="Utilisé pour identifier le contact",
                          copy=False)

    achats_option = fields.Selection([
        ('magasin', 'Au magasin'),
        ('siteweb', 'Depuis le siteweb'),
        ('Reseaux', 'Via réseaux'),

    ], string='Fait ces achats:')
