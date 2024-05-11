# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # barcode2 = fields.Char(string="Codebare", help="Utilisé pour identifier le contact",
    #                        copy=False)

    barcode2 = fields.Float(
        compute='_compute_amount_total_divided_by_50_sum',
        help="The sum of values of amount_total_divided_by_5 field for related customers",
    )

    def _compute_amount_total_divided_by_50_sum(self):
        for partner in self:
            # Retrieve all children partners and prefetch 'parent_id' on them
            all_partners = partner.with_context(active_test=False).search([('id', 'child_of', partner.ids)])
            all_partners.read(['parent_id'])

            barcode2 = 0
            pos_orders = self.env['pos.order'].search([('partner_id', 'in', all_partners.ids)])
            for order in pos_orders:
                barcode2 += order.amount_total_divided_by_50

            partner.barcode2 = int(barcode2)

    function_test = fields.Boolean(
        string="Function Triggered",
        default=False,
        help="This field becomes True whenever the function is triggered."
    )
    action_test_date = fields.Date(
        string="Action Test Date",
        help="Date when action_test function was triggered."
    )

    def action_test(self):
        self.function_test = True
        # Calculate the date one month from today
        today = datetime.today().date()
        one_month_later = today + timedelta(days=30)  # Adding 30 days to approximate one month
        self.action_test_date = one_month_later

    def action_test2(self):
        self.function_test = False


