# -*- coding: utf-8 -*-
{
    'name': "Website Sale Address City Selection",

    'summary': """Create Cities and select city for billing or shipping address""",

    'description': """This Module provide you a option to select your city for billing or shipping address in website. 
    These cities are created in back-end""",

    'author': "ErpMstar Solutions",
    'category': 'Website',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['website_sale', 'base_address_city'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'assets': {
        'web.assets_frontend': [
            '/website_sale_city_selection/static/src/js/city.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'application': True,
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 29,
    'currency': 'EUR',
}
