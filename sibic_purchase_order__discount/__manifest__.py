# -*- coding: utf-8 -*-
{
    'name': "SIBIC Purchase Percentage Discount",

    'summary': """
        Percentage Discount On Purchase Order 
        """,

    'description': """
        Adding a new custom fixed percentage discount field on Purchase Orde. 
    """,

    'images': ["static/description/main_banner.png"],
    'author': "Boucherit safaa",
    'company' : "SIBIC",
    'website': "http://sibic.dz/",
    'version': '15.0',
    'license': "AGPL-3",
    'category': "Purchase Management",


    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase'],

    # always loaded
    'data': [
        'views/purchase_order_view.xml',
    ]
}
