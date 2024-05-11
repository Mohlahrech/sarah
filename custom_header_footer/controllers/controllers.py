# -*- coding: utf-8 -*-
# from odoo import http


# class CustomHeaderFooter(http.Controller):
#     @http.route('/custom_header_footer/custom_header_footer', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_header_footer/custom_header_footer/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_header_footer.listing', {
#             'root': '/custom_header_footer/custom_header_footer',
#             'objects': http.request.env['custom_header_footer.custom_header_footer'].search([]),
#         })

#     @http.route('/custom_header_footer/custom_header_footer/objects/<model("custom_header_footer.custom_header_footer"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_header_footer.object', {
#             'object': obj
#         })
