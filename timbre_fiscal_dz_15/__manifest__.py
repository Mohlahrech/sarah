# -*- coding: utf-8 -*-
{
    'name': "Timbre Fiscal DZ",

    'summary': """
        Timbre fiscal algérien v15.0
        """,

    'description': """

    """,

    'author': "NUMIDIT",
    'website': "https://www.numidit.com/",


    'category': 'Sales Management',
    'version': '15.0.0.0',
    'license': 'LGPL-3',
    'currency': 'DZD',
    'price': '0.0',
    'depends': ['base', 'sale', 'purchase', 'account', 'sale_management'],

    'data': [
        'views/ks_account_account.xml',
        # 'views/ks_sale_order.xml',
        'views/ks_account_invoice.xml',
        # 'views/ks_purchase_order.xml',
        'views/ks_account_invoice_supplier_form.xml',
        'views/ks_report.xml',
        # 'views/assets.xml',

    ],

    'images': ['static/description/timbre_fiscal_dz_15_V15.jpg'],
    'assets': {
            'web.assets_backend': [
                '/timbre_fiscal_dz_15/static/css/ks_stylesheet.css',
            ],
        },

}
