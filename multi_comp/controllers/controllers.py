# -*- coding: utf-8 -*-
# from odoo import http


# class MultiMoh(http.Controller):
#     @http.route('/multi_comp/multi_comp', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/multi_comp/multi_comp/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('multi_comp.listing', {
#             'root': '/multi_comp/multi_comp',
#             'objects': http.request.env['multi_comp.multi_comp'].search([]),
#         })

#     @http.route('/multi_comp/multi_comp/objects/<model("multi_comp.multi_comp"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('multi_comp.object', {
#             'object': obj
#         })
