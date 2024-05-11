# -*- coding: utf-8 -*-
# from odoo import http


# class SibicCalculPrixVente(http.Controller):
#     @http.route('/sibic_calcul_prix_vente/sibic_calcul_prix_vente', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sibic_calcul_prix_vente/sibic_calcul_prix_vente/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sibic_calcul_prix_vente.listing', {
#             'root': '/sibic_calcul_prix_vente/sibic_calcul_prix_vente',
#             'objects': http.request.env['sibic_calcul_prix_vente.sibic_calcul_prix_vente'].search([]),
#         })

#     @http.route('/sibic_calcul_prix_vente/sibic_calcul_prix_vente/objects/<model("sibic_calcul_prix_vente.sibic_calcul_prix_vente"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sibic_calcul_prix_vente.object', {
#             'object': obj
#         })
