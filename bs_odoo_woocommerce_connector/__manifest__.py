# -*- coding: utf-8 -*-
{
    'name': "WooCommerce Odoo Connector",

    'summary': """
        Connect Odoo With WooCommerce""",
    'author': "Brain Station 23 LTD",
    'website': "http://www.brainstation-23.com",
    'license': 'OPL-1',
    'category': 'Sales',
    'version': '1.0',
    'depends': ['mail', 'account','sale_management','stock','delivery'],
    'external_dependencies': {
        'python': ['woocommerce'],
    },
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/product_category.xml',
        'views/log.xml',
        'views/menus.xml',
        'views/woocommerce_config.xml',
        'views/res_partner_views.xml',
        'views/product_template_views.xml',
        'views/sale_order.xml',
        'data/so_sequence.xml',
        'data/ir_cron.xml',
        'data/guest_partner.xml',

    ],
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
