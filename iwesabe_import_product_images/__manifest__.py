# -*- coding: utf-8 -*-
##############################################################################
#
#    Global Creative Concepts Tech Co Ltd.
#    Copyright (C) 2018-TODAY iWesabe (<https://www.iwesabe.com>).
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Import Product Images',
    'version': '15.0.0.0',
    'author': 'iWesabe',
    'summary': 'Import Product Images',
    'description': """This module for Import Products From Local Storage And URLs.""",
    'category': 'Products/ImportImages',
    'website': 'https://www.iwesabe.com/',
    'license': 'AGPL-3',
    'depends': ['product'],
    'data': [
		'security/ir.model.access.csv',
        'wizard/product_image_import_view.xml',
	],
    'assets': {
        'web.assets_backend': [
            'iwesabe_import_product_images/static/src/js/ListController.js',
        ],
        'web.assets_qweb': [
            'iwesabe_import_product_images/static/src/xml/**/*',
        ],
    },
    'qweb': [],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
