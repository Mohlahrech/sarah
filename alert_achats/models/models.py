from odoo import api, fields, models



class ProductPurchaseInfo(models.Model):
    _inherit = 'purchase.order.line'

    is_changed = fields.Boolean(string="Changed?", compute="compute_change")
    price_change = fields.Char(string="Alertes", readonly=True, default="N'oubliez de Maj le prix de vente!!")
    previous_price_unit = fields.Float(string="Previous Price Unit", store=True)

    @api.onchange('price_unit')
    def _onchange_price_unit(self):
        for record in self:
            record.previous_price_unit = record._origin.price_unit

    @api.depends('price_unit', 'previous_price_unit')
    def compute_change(self):
        for record in self:
            if record.price_unit != record.previous_price_unit:
                        record.is_changed = True
            else:
                        record.is_changed = False















