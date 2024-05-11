# -*- coding: utf-8 -*-


from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SibicFactureCachet(models.Model):

    _inherit = 'account.move'
    _description = 'Ajout dun booleen pour controler limpression des factures'

    cachet = fields.Boolean(
        string='Imprimer avec cachet',
        default=False,
    )
    

class SibicCalculPrixVenteProduit(models.Model):

    _inherit = 'product.template'
    _description = 'Ajout du champ marge et definition du calcul du prix de vente'

    detailed_type = fields.Selection(
        default='product'
    )
    standard_price = fields.Float(
        required=True
    )
    marge = fields.Float(
        string='Marge',
        required=True,
        readonly=False,
        help='marge beneficiere en pourcentage',
        default=40
    )

    @api.constrains('list_price', 'strandard_price')
    def _check_date_end(self):
        for record in self:
            if record.list_price < record.standard_price:
                raise ValidationError(
                    "Le prix de vente ne peut etre inferieur au cout.")

    @api.onchange("standard_price")
    def _onchange_standard_price(self):
        self.list_price = round(self.standard_price*(100+self.marge)/100)

    @api.onchange("marge")
    def _onchange_marge(self):
        if self.marge < 1:
            raise ValidationError(
                "La marge ne peut etre inferieur à 1 cela va entrainer un prix de vente inferieur au cout.")
            self._onchange_list_price()

        else:
            self.list_price = round(self.standard_price*(100+self.marge)/100)

    @api.onchange("list_price")
    def _onchange_list_price(self):
        if self.standard_price != 0:
            self.marge = round(self.list_price*100/self.standard_price - 100)


class SibicCalculPrixVenteVar(models.Model):

    _inherit = 'product.product'
    _description = 'Ajout du champ marge et definition du calcul du prix de vente a achat'

    
    standard_price = fields.Float(
        required=True
    )
    marge = fields.Float(
        string='Marge',
        required=True,
        readonly=False,
        help='marge beneficiere en pourcentage',
        default=40
    )

    @api.constrains('list_price', 'strandard_price')
    def _check_date_end(self):
        for record in self:
            if record.list_price < record.standard_price:
                raise ValidationError(
                    "Le prix de vente ne peut etre inferieur au cout.")

    @api.onchange("standard_price")
    def _onchange_standard_price(self):
        self.list_price = round(self.standard_price*(100+self.marge)/100)

    @api.onchange("marge")
    def _onchange_marge(self):
        if self.marge < 1:
            raise ValidationError(
                "La marge ne peut etre inferieur à 1 cela va entrainer un prix de vente inferieur au cout.")
            self._onchange_list_price()

        else:
            self.list_price = round(self.standard_price*(100+self.marge)/100)

    @api.onchange("list_price")
    def _onchange_list_price(self):
        if self.standard_price != 0:
            self.marge = round(self.list_price*100/self.standard_price - 100)
