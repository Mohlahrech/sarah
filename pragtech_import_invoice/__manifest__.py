# -*- coding: utf-8 -*-
{
    'name': 'Odoo Import Invoice Data',
    'version': '15.0.0.1',
    'category': 'Extra Tools',
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'website': 'www.pragtech.co.in',
    'summary': 'Import Invoice From CSV and Excel File To Odoo import invoice data importing invoices odoo import invoices',
    'description': """
Odoo Import Invoice Data
========================
Import invoice from CSV and Excel file.

<keywords>
Import invoices
import invoice data
importing invoices
odoo import invoices
""",
    'depends': ['base', 'sale_management', 'stock', 'account', ],
    'data': [
        'security/ir.model.access.csv',
        'security/import_security_invoice.xml',
        'views/invoice_view.xml',
    ],
    'images': ['static/Animated-import-invoice-data.gif'],
    'live_test_url': 'https://www.pragtech.co.in/company/proposal-form.html?id=310&name=support-odoo-import-invoice-data',
    'license': 'OPL-1',
    'price': 10,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
}
