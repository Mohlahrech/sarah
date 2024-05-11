# -*- coding: utf-8 -*-

from odoo import models, fields


class SynchronizationLog(models.Model):
    _name = 'synchronization.log'
    _description = "Synchronization Log"
    _rec_name = 'operation_type'
    _order = 'id desc'

    operation_type = fields.Selection([('import', 'Import')], required=True)
    response = fields.Text('Description')
    status_code = fields.Integer('Status Code')
    model = fields.Char('Model')
    url = fields.Char('Url')
    method = fields.Char('Api Method', groups='base.group_no_one')
    message = fields.Text('Message')
    failed_ids = fields.Text('Failed Ids')
    operation_on = fields.Selection([('product', 'Product'),
                                     ('category', 'Product Category'),
                                     ('attribute', 'Product Attribute'),
                                     ('order', 'Order'),
                                     ('shipping_method', 'Shipping Method'),
                                     ('tax', 'Tax'),
                                     ('customer', 'Customer')])
    company_id = fields.Many2one('res.company', 'Company', readonly=True, default=lambda self: self.env.user.company_id)