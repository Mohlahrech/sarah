# -*- coding: utf-8 -*-

import binascii
import logging
import tempfile
from datetime import datetime

import xlrd
from odoo import models, fields, exceptions, _
from odoo.exceptions import Warning, UserError

_logger = logging.getLogger(__name__)
import io

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class AccountMove(models.Model):
    _inherit = "account.move"

    custom_sequence = fields.Boolean('Custom Sequence')
    system_sequence = fields.Boolean('System Sequence')
    sequence_number_next = fields.Char(string='Next Number', store=True)


class ImportAccountInvoice(models.TransientModel):
    _name = "import.account.invoice"

    file = fields.Binary('File')
    account_available = fields.Selection(
        [('default', 'Use Account From Configuration product/Property'), ('custom', 'Use Account From Excel/CSV')],
        string='Select Account', required=True, default='default')
    type = fields.Selection([('in', 'Customer'), ('out', 'Supplier')], string=' Choice', required=True, default='in')
    sequence_available = fields.Selection(
        [('custom', 'Use Excel/CSV Sequence Number'), ('system', 'Use System Default Sequence Number')],
        string='Sequence Available', default='custom')
    import_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')
    invoice_stage = fields.Selection(
        [('draft', 'Import Invoices in  Draft Stage'), ('confirm', 'Validate Invoices Automatically while Importing')],
        string="Invoice Stages", default='draft')
    import_product_search = fields.Selection([('by_code', 'Search By Code'), ('by_name', 'Search By Name'), ('by_ids', 'Search By ID')],
                                             string='Product Search Option',default='by_code')

    def make_account_invoice(self, values):
        invoice_obj = self.env['account.move']
        if self.type == "in":
            invoice_search = invoice_obj.search([
                ('name', '=', values.get('invoice')),
                ('move_type', '=', 'out_invoice')
            ])
        else:
            invoice_search = invoice_obj.search([
                ('name', '=', values.get('invoice')),
                ('move_type', '=', 'in_invoice')
            ])
        if invoice_search:
            if invoice_search.partner_id.name == values.get('customer'):
                if invoice_search.currency_id.name == values.get('currency'):
                    # if invoice_search.invoice_user_id.name == values.get('salesperson'):
                        # self.make_account_invoice_line(values, invoice_search)
                        return invoice_search
                    # else:
                        # raise Warning(_('User(Salesperson) is different for "%s" .\n Please define same.') % values.get(
                            # 'invoice'))
                else:
                    raise Warning(_('Currency is different for "%s" .\n Please define same.') % values.get('invoice'))
            else:
                raise Warning(_('Customer name is different for "%s" .\n Please define same.') % values.get('invoice'))
        else:
            partner_id = self.search_partner(values.get('customer'))
            currency_id = self.search_currency(values.get('currency'))
            # salesperson_id = self.search_sales_person(values.get('salesperson'))
            inv_date = self.search_invoice_date(values.get('date'))
            print("inv_date", inv_date)

            if self.type == "in":
                type_inv = "out_invoice"
                if partner_id.property_account_receivable_id:
                    account_id = partner_id.property_account_receivable_id
                else:
                    account_search = self.env['ir.property'].search([('name', '=', 'property_account_receivable_id')])
                    account_id = account_search.value_reference
                    if not account_id:
                        raise UserError(_('Please define Customer account.'))
                    account_id = account_id.split(",")[1]
                    account_id = self.env['account.account'].browse(account_id)
            else:
                if partner_id.property_account_payable_id:
                    account_id = partner_id.property_account_payable_id
                else:
                    account_search = self.env['ir.property'].search([('name', '=', 'property_account_payable_id')])
                    account_id = account_search.value_reference
                    if not account_id:
                        raise UserError(_('Please define Vendor account.'))
                    account_id = account_id.split(",")[1]
                    account_id = self.env['account.account'].browse(account_id)
                type_inv = "in_invoice"
            if values.get('seq_opt') == 'system':
                journal = self.env['account.move']._get_default_journal()
                if journal.secure_sequence_id:
                    # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
                    sequence = journal.secure_sequence_id
                    name = sequence.with_context(
                        ir_sequence_date=datetime.today().date().strftime("%Y-%m-%d")).next_by_id()
                    temp_name = name.split('/')
                    add_end = ''
                    if temp_name:
                        if int(temp_name[-1]) >= 0 and int(temp_name[-1]) <= 9:
                            add_end = '000' + str(int(temp_name[-1]) + 1)
                        elif int(temp_name[-1]) >= 10 and int(temp_name[-1]) <= 99:
                            add_end = '00' + str(int(temp_name[-1]) + 1)
                        elif int(temp_name[-1]) >= 100 and int(temp_name[-1]) <= 999:
                            add_end = '0' + str(int(temp_name[-1]) + 1)
                        else:
                            add_end = str(int(temp_name[-1]) + 1)

                        first_part = temp_name[0]
                        second_part = temp_name[0]

                        temp_name = str(first_part) + "/" + str(second_part) + "/" + add_end
                        name = temp_name



                else:
                    raise UserError(_('Please define a sequence on the journal.'))
            else:
                name = values.get('invoice')
            temp_name = name
            temp_name = temp_name.split('/')[-1]

            inv_id = invoice_obj.create({
                'partner_id': partner_id.id,
                'currency_id': currency_id.id,
                # 'invoice_user_id': salesperson_id.id,
                'name': name,
                'custom_sequence': True if values.get('seq_opt') == 'custom' else False,
                'system_sequence': True if values.get('seq_opt') == 'system' else False,
                'move_type': type_inv,
                'invoice_date': inv_date,
                'sequence_number_next': temp_name,
            })
            inv_id.sequence_number_next = temp_name
            self.make_account_invoice_line(values, inv_id)
            # inv_id.compute_taxes()
            return inv_id

    def make_account_invoice_line(self, values, inv_id):
        product_obj = self.env['product.product']
        product_uom = self.env['uom.uom'].search([('name', '=', values.get('uom'))])
        tax_ids = []
        product_id = ''
        # Search By Product
        try:
            if self.import_product_search == 'by_code':
                product_id = product_obj.search([('default_code', '=', values.get('product'))])
            elif self.import_product_search == 'by_name':
                product_id = product_obj.search([('name', '=', values.get('product'))])
            elif self.import_product_search == 'by_ids':
                product_id = product_obj.search([('id', '=', values.get('product'))])
            if not product_id:
                product_id = product_obj.create({'name': values.get('product')})

        except Exception:
            raise UserError(_("Product not present. For creating new product please provide product name"))



        if inv_id.move_type == 'out_invoice':
            if values.get('tax'):
                if ';' in values.get('tax'):
                    tax_names = values.get('tax').split(';')
                    for name in tax_names:
                        tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'sale')])
                        if not tax:
                            raise Warning(_('"%s" Tax not available in  your system') % name)
                        tax_ids.append(tax.id)

                elif ',' in values.get('tax'):
                    tax_names = values.get('tax').split(',')
                    for name in tax_names:
                        tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'sale')])
                        if not tax:
                            raise Warning(_('"%s" Tax not available in your system') % name)
                        tax_ids.append(tax.id)
                else:
                    tax_names = values.get('tax').split(',')
                    tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'sale')])
                    if not tax:
                        raise Warning(_('"%s" Tax not available in your system') % tax_names)
                    tax_ids.append(tax.id)
        else:
            if values.get('tax'):
                if ';' in values.get('tax'):
                    tax_names = values.get('tax').split(';')
                    for name in tax_names:
                        tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                        if not tax:
                            raise Warning(_('"%s" Tax not available in your system') % name)
                        tax_ids.append(tax.id)

                elif ',' in values.get('tax'):
                    tax_names = values.get('tax').split(',')
                    for name in tax_names:
                        tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                        if not tax:
                            raise Warning(_('"%s" Tax not available in your system') % name)
                        tax_ids.append(tax.id)
                else:
                    tax_names = values.get('tax').split(',')
                    tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'purchase')])
                    if not tax:
                        raise Warning(_('"%s" Tax not available in your system') % tax_names)
                    tax_ids.append(tax.id)

        if not product_uom:
            raise Warning(_(' "%s" Product UOM category is not present.') % values.get('uom'))
        if self.account_available == 'default':
            if inv_id.move_type == 'out_invoice':
                if product_id.property_account_income_id:
                    account = product_id.property_account_income_id
                elif product_id.categ_id.property_account_income_categ_id:
                    account = product_id.categ_id.property_account_income_categ_id
                else:
                    account_search = self.env['ir.property'].search([('name', '=', 'property_account_income_categ_id')])
                    account = account_search.value_reference
                    account = account.split(",")[1]
                    account = self.env['account.account'].browse(account)
            if inv_id.move_type == 'in_invoice':
                if product_id.property_account_expense_id:
                    account = product_id.property_account_expense_id
                elif product_id.categ_id.property_account_expense_categ_id:
                    account = product_id.categ_id.property_account_expense_categ_id
                else:
                    account_search = self.env['ir.property'].search(
                        [('name', '=', 'property_account_expense_categ_id')])
                    account = account_search.value_reference
                    account = account.split(",")[1]
                    account = self.env['account.account'].browse(account)

        else:
            if values.get('account') == '':
                raise Warning(_(' You can not left blank account field if you select Excel/CSV Account Option'))
            else:
                if self.import_file == 'csv':
                    account_id = self.env['account.account'].search([('code', '=', values.get('account'))])
                else:
                    acc = values.get('account').split('.')
                    account_id = self.env['account.account'].search([('code', '=', acc[0])])
                if account_id:
                    account = account_id
                else:
                    raise Warning(_(' "%s" Account is not present.') % values.get('account'))

        vals_ol = {}
        vals_col = {}
        vals_tol = {}

        if inv_id:
            vals_ol.update({'move_id': inv_id.id})
            vals_col.update({'move_id': inv_id.id})
            vals_tol.update({'move_id': inv_id.id})

        if product_id:
            vals_ol.update({'product_id': product_id.id})
            vals_col.update({'product_id': False})
            vals_tol.update({'product_id': False})

        if tax_ids:
            vals_ol.update({'tax_ids': [(6, 0, tax_ids)]})
            vals_col.update({'tax_ids': False})
            vals_tol.update({'tax_ids': False})

        else:
            vals_ol.update({'tax_ids': False})
            vals_col.update({'tax_ids': False})
            vals_tol.update({'tax_ids': False})

        if account:
            vals_ol.update({'account_id': account.id})

        if inv_id.partner_id.property_account_receivable_id:
            vals_col.update({'account_id': inv_id.partner_id.property_account_receivable_id.id})

        if tax_ids:
            acc_id = self.env['account.tax.repartition.line'].search(
                [('invoice_tax_id', '=', tax_ids[0]), ('repartition_type', '=', 'tax')], limit=1)
            if acc_id.account_id:
                vals_tol.update({'account_id': acc_id.account_id.id})

        vals_ol.update({
            'quantity': float(values.get('quantity')) if values.get('quantity') else 0.00,
            'name': values.get('description') if values.get('description') else '',
            'exclude_from_invoice_tab': False,
        })

        vals_col.update({
            'quantity': float(values.get('quantity')) if values.get('quantity') else 0.00,
            'name': False,
            'exclude_from_invoice_tab': True,
        })

        vals_tol.update({
            'quantity': float(values.get('quantity')) if values.get('quantity') else 0.00,
            'name': False,
            'exclude_from_invoice_tab': True,
        })

        if 'price' in values and values.get('price') != 'None':
            vals_ol.update({'price_unit': float(values.get('price'))})
            vals_col.update({'price_unit': -(float(values.get('price')))})

            vals_ol.update({'credit': vals_ol['quantity'] * float(values.get('price'))})
            vals_ol.update({'debit': 0})

            vals_col.update({'credit': 0})
            vals_col.update({'debit': vals_col['quantity'] * (float(values.get('price')))})
        else:
            vals_ol.update({'price_unit': 0})
            vals_col.update({'price_unit': 0})

            vals_ol.update({'credit': 0})
            vals_ol.update({'debit': 0})

            vals_col.update({'credit': 0})
            vals_col.update({'debit': 0})

        if vals_ol.get('tax_ids'):
            tax_amount = tax.amount
            vals_tol['price_unit'] = float(vals_ol['quantity'] * vals_ol['price_unit'] * float(tax_amount / 100))
            vals_tol['credit'] = vals_tol['price_unit']
            vals_tol['debit'] = 0

            vals_col['debit'] += vals_tol['credit']

            vals_ol['tax_repartition_line_id'] = False
            vals_col['tax_repartition_line_id'] = False
            tax_repartition_line_id = self.env['account.tax.repartition.line'].search(
                [('repartition_type', '=', 'tax')], limit=1)
            vals_tol['tax_repartition_line_id'] = tax_repartition_line_id.id

            vals_ol['tax_base_amount'] = 0
            vals_col['tax_base_amount'] = 0
            vals_tol['tax_base_amount'] = vals_ol['quantity'] * vals_ol['price_unit']
        else:
            vals_tol.update({'price_unit': 0})
            vals_tol.update({'credit': 0})
            vals_tol.update({'debit': 0})

        if vals_ol and vals_col:
            data = []
            data.append(vals_ol)
            data.append(vals_col)
            if vals_ol.get('tax_ids'):
                data.append(vals_tol)
            invoice_line_id = self.env['account.move.line'].create(data)
        return True

    def search_currency(self, name):
        currency_obj = self.env['res.currency']
        currency_search = currency_obj.search([('name', '=', name)])
        if currency_search:
            return currency_search
        else:
            raise Warning(_(' "%s" Currency are not present.') % name)

    # def search_sales_person(self, name):
        # sals_person_obj = self.env['res.users']
        # partner_search = sals_person_obj.search([('name', '=', name)])
        # if partner_search:
            # return partner_search
        # else:
            # raise Warning(_('Invalid Salesperson Name "%s"') % name)

    def search_partner(self, name):
        partner_obj = self.env['res.partner']
        partner_search = partner_obj.search([('name', '=', name)])
        if partner_search:
            return partner_search
        else:
            partner_id = partner_obj.create({
                'name': name})
            return partner_id

    def search_invoice_date(self, date):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        print("date", date)
        i_date = datetime.strptime(str(date), DATETIME_FORMAT)
        return i_date.date()

    def import_csv(self):
        """Load Inventory data from the CSV file."""
        if self.import_file == 'csv':

            try:
                csv_data = base64.b64decode(self.file)
                data_file = io.StringIO(csv_data.decode("windows-1252"))
                data_file.seek(0)
                file_reader = []
                csv_reader = csv.reader(data_file, delimiter=',')
            except Exception:
                raise exceptions.Warning(_("Please upload csv file !"))
            except Exception as ex:
                raise exceptions.Warning(str(ex))

            try:
                file_reader.extend(csv_reader)
            except Exception:
                raise exceptions.Warning(_("Invalid file!"))

            if self.account_available == 'default':
                if len(file_reader[0]) == 10:
                    keys = ['invoice', 'customer', 'currency', 'product', 'quantity', 'uom', 'description', 'price',
                            'tax', 'date']

                elif len(file_reader[0]) > 10:
                    raise Warning(
                        _(
                            'As you select use Account from configuration Product/Property . Please remove Account column from CSV /Excel file !'))
                else:
                    raise Warning(_('Your File has less columns . Please provide required columns'))
            else:
                if len(file_reader[0]) == 11:
                    keys = ['invoice', 'customer', 'currency', 'product', 'account', 'quantity', 'uom', 'description',
                            'price', 'tax',
                            'date']

                elif len(file_reader[0]) > 11:
                    raise Warning(_('Your File has extra columns !'))
                else:
                    raise Warning(_(
                        'As you select use Account from configuration Product/Property . Please Add Account column after PRODUCT column in  CSV /Excel file !'))
            values = {}
            for i in range(len(file_reader)):
                field = list(map(str, file_reader[i]))
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        values.update(
                            {'move_type': self.type, 'option': self.import_file, 'seq_opt': self.sequence_available})
                        res = self.make_account_invoice(values)
                        if self.invoice_stage == 'confirm':
                            if res.state in ['draft']:
                                res.post()
        else:
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            try:
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise exceptions.Warning(_("Please upload xlsx file !"))
            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = map(lambda row: row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    get_line = list(
                        map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                            sheet.row(row_no)))
                    if self.account_available == 'default':
                        if len(get_line) == 10:
                            a1 = get_line[9]
                            datetime_date = xlrd.xldate_as_datetime(float(a1), 0)
                            date_object = datetime_date.date()
                            string_date = datetime_date.isoformat()
                            print('datetime_date :', string_date, datetime_date)
                            date_string = datetime.strptime(str(datetime_date),'%Y-%m-%d %H:%M:%S')
                            values.update({'invoice': get_line[0],
                                           'customer': get_line[1],
                                           'currency': get_line[2],
                                           'product': get_line[3],
                                           'quantity': float(get_line[4]),
                                           'uom': get_line[5],
                                           'description': get_line[6],
                                           'price': float(get_line[7]),
                                           'tax': get_line[8],
                                           'date': date_string,
                                           'seq_opt': self.sequence_available
                                           })
                        elif len(get_line) > 10:
                            raise Warning(_(
                                'As you select use Account from configuration Product/Property . Please remove Account column from CSV /Excel file !'))
                        else:
                            raise Warning(_('Your File has less columns . Please provide required columns'))
                    else:
                        if len(get_line) == 11:
                            a1 = get_line[10]
                            date_string = datetime.strptime(str(a1),'%Y-%m-%d %H:%M:%S')
                            values.update({'invoice': get_line[0],
                                           'customer': get_line[1],
                                           'currency': get_line[2],
                                           'product': get_line[3],
                                           'account': get_line[4],
                                           'quantity': float(get_line[5]),
                                           'uom': get_line[6],
                                           'description': get_line[7],
                                           'price': float(get_line[8]),
                                           'tax': get_line[9],
                                           'date': date_string,
                                           'seq_opt': self.sequence_available
                                           })
                        elif len(get_line) > 10:
                            raise Warning(_('Your File has extra columns !'))
                        else:
                            raise Warning(_(
                                'As you select use Account from configuration Product/Property . Please Add Account column after PRODUCT column in  CSV /Excel file !'))
                    res = self.make_account_invoice(values)
                    if self.invoice_stage == 'confirm':
                        if res.state in ['draft']:
                            res.post()

        return res
