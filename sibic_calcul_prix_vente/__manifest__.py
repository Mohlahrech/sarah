# -*- coding: utf-8 -*-
{
    'name': "Sibic compute sales price",


    'description': """
        Tous les articles soient stockables par défaut 
        Champs coût de l'article obligatoire
        Ajout d’un champs marge pour chaque produit
        Calcul du champ prix de vente en fonction du coût et de la marge
        Interdire que le prix de vente soit inférieur au coût
    """,

    'author': "BOUCHERIT Safaa",
    'website': "http://sibic.dz/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'sale_management'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/product_template_inherit.xml',
    ],
    'license': 'LGPL-3',
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
