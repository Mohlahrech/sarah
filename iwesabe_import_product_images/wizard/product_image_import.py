# -*- coding: utf-8 -*-

import base64
import io
import csv
import xlrd
import urllib
from odoo import models, fields, api, modules, _

def _format_cell(cell_value):
	if not cell_value:
		return False
	if isinstance(cell_value, float):
		cell_value = str(int(cell_value))
	elif isinstance(cell_value, int):
		cell_value = str(int(cell_value))
	return cell_value

def _get_image_info(image_1920):
	image = False
	if not image_1920:
		return image
	image_1920 = image_1920.strip()
	if 'http' in image_1920 or 'https' in image_1920:
		request = urllib.request.Request
		url = image_1920
		check_url = request(url, headers={'User-Agent': 'Mozilla/5.0'})
		bytes_type_img = urllib.request.urlopen(check_url).read()
		image = base64.encodebytes(bytes_type_img)
	else:
		bytes_type_img = open(image_1920, 'rb').read()
		image = base64.b64encode(bytes_type_img)
	return image


class ProductImportImage(models.TransientModel):
	_name = 'product.import.image'
	_description = 'Product Import Image'
	
	file = fields.Binary('File')
	filename = fields.Char('')

	def action_import(self):
		self = self.sudo()
		if not self._context.get('model_name'):
			return
		if not self.file:
			return
		model_name = self._context.get('model_name')
		file_format = self.filename.split('.')[-1]
		if file_format == 'csv':
			return self._csv_format(model_name)
		elif file_format in ['xlsx', 'xls']:
			return self._xls_format(model_name)

	def _csv_format(self, model_name=None):
		csv_data = base64.b64decode(self.file)
		data_file = io.StringIO(csv_data.decode('utf-8'))
		data_file.seek(0)
		file_reader = []
		csv_reader = csv.reader(data_file, delimiter=',')
		file_reader.extend(csv_reader)
		row = 1
		updated_image_products = []
		for csv_file in file_reader[1:]:
			product_barcode = csv_file[0]
			product_name = csv_file[1]
			product_default_code = csv_file[2]
			image_1920 = csv_file[3]
			image_info = _get_image_info(image_1920)
			product_ids = self.env[model_name]
			if _format_cell(product_barcode):
				product_ids = self.env[model_name].search([('barcode',
						'=', _format_cell(product_barcode))])
			if not product_ids and product_name:
				product_ids = self.env[model_name].search([('name',
						'ilike', product_name.strip())])
			if not product_ids and _format_cell(product_default_code):
				product_ids = \
					self.env[model_name].search([('default_code', '=',
						_format_cell(product_default_code))])
			if product_ids and image_info:
				product_ids.update({'image_1920': image_info})
				updated_image_products.extend(product_ids.ids)
			row += 1
		return {
			'name': _('Updated Image Products'),
			'type': 'ir.actions.act_window',
			'res_model': model_name,
			'views': [(False, 'kanban'), (False, 'tree'), (False, 'form')],
			'view_mode': 'kanban,tree,form',
			'domain': [('id', 'in', updated_image_products)],
			}

	def _xls_format(self, model_name=None):
		try:
			book = xlrd.open_workbook(file_contents=base64.decodebytes(self.file))
			sheet = book.sheet_by_index(0)
			sheet.row_slice
			TotalCol = len(sheet.col(0))
			rows = 0
		except Exception as e:
			raise Warning(_(e))

		updated_image_products = []
		for col in range(TotalCol):
			if rows == 0:
				rows += 1
				continue

			product_barcode = sheet.cell_value(rows, 0)
			product_name = sheet.cell_value(rows, 1)
			product_default_code = sheet.cell_value(rows, 2)
			image_1920 = sheet.cell_value(rows, 3)

			image_info = _get_image_info(image_1920)

			product_ids = self.env[model_name]
			if _format_cell(product_barcode):
				product_ids = self.env[model_name].search([('barcode',
						'=', _format_cell(product_barcode))])
			if not product_ids and product_name:
				product_ids = self.env[model_name].search([('name',
						'ilike', product_name.strip())])
			if not product_ids and _format_cell(product_default_code):
				product_ids = \
					self.env[model_name].search([('default_code', '=',
						_format_cell(product_default_code))])

			if product_ids and image_info:
				product_ids.update({'image_1920': image_info})
				updated_image_products.extend(product_ids.ids)
			rows += 1

		return {
			'name': _('Updated Image Products'),
			'type': 'ir.actions.act_window',
			'res_model': model_name,
			'views': [(False, 'kanban'), (False, 'tree'), (False, 'form'
					  )],
			'view_mode': 'kanban,tree,form',
			'domain': [('id', 'in', updated_image_products)],
			}
