# -*- coding: utf-8 -*-
{
    'name': "Product Stock Alert",
    'version': '15.0.1.0.0',
    'summary': """Product Stock Alert""",
    "category": 'Inventory',
    'description': """Product Stock Alert""",
    'author': 'SIBIC',
    'company': 'SIBIC',
    'maintainer': 'SIBIC',
    'website': 'http://www.sibic.dz',
    'depends': ['base', 'sale_management', 'stock', 'point_of_sale', 'product'],
    'data': [
        'security/security.xml',
        'views/res_config_settings_views.xml',
        'views/product_product_views.xml',
        'views/product_template_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'low_stocks_product_alert/static/src/js/alert_color_js.js',
            'low_stocks_product_alert/static/src/css/style.css',
        ],
        'point_of_sale.assets': [
            'low_stocks_product_alert/static/src/js/alert_tag_js.js',
        ],
        'web.assets_qweb': [
            'low_stocks_product_alert/static/src/xml/alert_tag_js.xml',
        ],
    },
    'license': "LGPL-3",
    'installable': True,
    'application': True
}
