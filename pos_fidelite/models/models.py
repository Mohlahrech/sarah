# -*- coding: utf-8 -*-

from odoo import models, fields, api
#from datetime import datetime, timedelta

class pos_fidelite(models.Model):
        _inherit = "pos.order"

        amount_total = fields.Float(string='Total', digits=0, readonly=True, required=True)

        amount_total_divided_by_50 = fields.Float(string='Points de fidélité', readonly=True,
                                                  compute='_compute_amount_total_divided_by_50')

        date_order = fields.Datetime(string='Date', readonly=True, index=True, default=fields.Datetime.now)

        @api.depends('amount_total')
        def _compute_amount_total_divided_by_50(self):
            for record in self:
                record.amount_total_divided_by_50 = record.amount_total / 50

#pour calculer la fidélité apartir dun date bien précise
        # amount_total = fields.Float(string='Total', digits=0, readonly=True, required=True)
        # amount_total_divided_by_50 = fields.Float(string='Points de fidélité', readonly=True,
        #                                           compute='_compute_amount_total_divided_by_50')
        # date_order = fields.Datetime(string='Date', readonly=True, index=True, default=fields.Datetime.now)
        #
        # @api.depends('amount_total', 'date_order')
        # def _compute_amount_total_divided_by_50(self):
        #     for record in self:
        #         # Calculate today's date
        #         today_date = datetime.now()
        #
        #         # Calculate the date one month ago
        #         one_month_ago = today_date - timedelta(days=30)
        #
        #         # Check if the date_order is less than one month from today's date
        #         if record.date_order >= one_month_ago:
        #             # If the condition is met, calculate the amount_total_divided_by_50
        #             record.amount_total_divided_by_50 = record.amount_total / 50
        #         else:
        #             # If the condition is not met, set the field to zero
        #             record.amount_total_divided_by_50 = 0
