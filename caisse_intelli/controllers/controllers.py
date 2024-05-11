# -*- coding: utf-8 -*-
# from odoo import http


# class CaisseIntelli(http.Controller):
#     @http.route('/caisse_intelli/caisse_intelli', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/caisse_intelli/caisse_intelli/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('caisse_intelli.listing', {
#             'root': '/caisse_intelli/caisse_intelli',
#             'objects': http.request.env['caisse_intelli.caisse_intelli'].search([]),
#         })

#     @http.route('/caisse_intelli/caisse_intelli/objects/<model("caisse_intelli.caisse_intelli"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('caisse_intelli.object', {
#             'object': obj
#         })
