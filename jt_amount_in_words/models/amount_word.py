from odoo import api, fields, models

class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.depends('amount_total', 'currency_id')
    def _compute_amount_in_word(self):
        for rec in self:
            if rec.currency_id and rec.amount_total:
                rec.num_word = str(rec.currency_id.amount_to_text(rec.amount_total))
            else:
                rec.num_word = False

    num_word = fields.Char(string="Arrêté la présente commande/devis à la somme de: ", compute='_compute_amount_in_word', store=True)


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    @api.depends('amount_total', 'currency_id')
    def _compute_amount_in_word(self):
        for rec in self:
            if rec.currency_id and rec.amount_total:
                rec.num_word = str(rec.currency_id.amount_to_text(rec.amount_total))
            else:
                rec.num_word = False

    num_word = fields.Char(string="Arrêté la présente commande à la somme de: ", compute='_compute_amount_in_word', store=True)


class InvoiceOrder(models.Model):

    _inherit = 'account.move'

    @api.depends('amount_total', 'currency_id')
    def _compute_amount_in_word(self):
        for rec in self:
            if rec.currency_id and rec.amount_total:
                rec.num_word = str(rec.currency_id.amount_to_text(rec.amount_total))
            else:
                rec.num_word = False

    num_word = fields.Char(string="Arrêté la présente facture à la somme de: ", compute='_compute_amount_in_word', store=True)

