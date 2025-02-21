# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Restriction quantité zero',
    'version': '15.0.0.1',
    'category': 'Point of Sale',
    'summary': 'Point Of Sale Restrict Zero Quantity pos restrict negative stock sales of products with zero or negative stock levels pos restrict zero stock product pos Restrict product with zero Quantity pos order line restriction with zero Quantity on pos',
    'description' :"""
       The Point Of Sale Restrict Zero Quantity Odoo App helps users to prevents the sales of products with zero or negative stock levels, ensuring that businesses never run out of stock. Additionally, the app can be configured to display a warning message when the stock level of a product is getting low. When a customer attempts to purchase a product with a stock level below the minimum, the app will display an error message, preventing the sale from going through.
    """,
    'author': 'Moh',
    'website': 'Moh',
    'depends': ['base','point_of_sale'],
    'data': [
        'views/pos_config_view.xml',
    ],
    'assets':{
        'point_of_sale.assets': [
            '/bi_pos_restrict_zero_qty/static/src/js/models.js',
            '/bi_pos_restrict_zero_qty/static/src/js/ProductScreen.js',
         ],
    },
    'demo': [],
    'test': [],
    'license':'OPL-1',
    'installable': True,
    'auto_install': False,
    "images":['static/description/Banner.gif'],
}
