# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)



    @api.constrains('company_id')
    def _check_company(self):
        for record in self:
            if not record.company_id:
                raise ValidationError("Veuillez remplir le champ société.")


