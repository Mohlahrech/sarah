from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PoCachet(models.Model):
    _inherit = 'purchase.order'
    _description = 'Ajout dun booleen pour controler limpression des factures'

    cachet = fields.Boolean(
        string='Imprimer avec cachet',
        default=False,
    )
