

from odoo import api, fields, models

class SibicPurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sibic_discount = fields.Float(
        string='Disc %.', 
        digits='Discount', 
        default=0.000
        )
    @api.onchange("sibic_discount")
    def _onchange_sibic_discount(self):
        for record in self.order_line:
            record.price_subtotal= record.price_unit * (1 - (record.discount / 100.0))*record.product_qty
            taxes = record.taxes_id.compute_all(**record._prepare_compute_all_values())
            record.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
   
class SibicPurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"


    discount = fields.Float(
        string='% Disc.', 
        digits='Discount', 
        compute= "_compute_discount"
        )

    @api.depends("order_id.sibic_discount")
    def _compute_discount(self):
        for record in self:
            record.discount=record.order_id.sibic_discount
            
            
            



    def _prepare_compute_all_values(self):
        # Hook method to returns the different argument values for the
        # compute_all method, due to the fact that discounts mechanism
        # is not implemented yet on the purchase orders.
        # This method should disappear as soon as this feature is
        # also introduced like in the sales module.
        self.ensure_one()
        price_unit_w_discount = self.price_unit
        if self.discount != 0:
            price_unit_w_discount = self.price_unit * (1 - (self.discount / 100.0))

        return {
            'price_unit': price_unit_w_discount,
            'currency': self.order_id.currency_id,
            'quantity': self.product_qty,
            'product': self.product_id,
            'partner': self.order_id.partner_id,
        }
