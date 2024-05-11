# -*- coding: utf-8 -*-
{
    'name': "multi_comp",

    'summary': """
        module ajouté""",

    'description': """
        Renseigne automatiquement le champ société lors de la création d'un article paraport à la société affichée, force l'utilisateur
        a remplir le champ société
    """,

    'author': "Moh",
    'website': "https://cv-lahrech-mohamed.onrender.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
