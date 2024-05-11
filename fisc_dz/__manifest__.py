# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright (c) 2016  

{
    'name': 'Algeria - Fisc Info',
    'version': '15.0',
    'category': 'Localization',
    'description': """
This is the module to manage the fisc info for Algeria in Odoo.
========================================================================

This module applies to companies based in Algeria.
.

""",
    'author': 'NumidIT',
    'website': 'http://www.NumidIT.dz',
    'depends': ['account'],
    'data': [
        'views/fisc_dz_view.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
