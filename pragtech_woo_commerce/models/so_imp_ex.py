# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning
from woocommerce import API
from odoo.tools import float_is_zero, html_keep_url, is_html_empty
from markupsafe import Markup
from odoo.tools import config
config['limit_time_real'] = 1000000

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    woo_id = fields.Char('WooCommerce ID')
    payment_type = fields.Selection([('cod', 'COD'), ('prepaid', 'Prepaid')], "Payment Type")
    is_exported = fields.Boolean('Synced In Woo', default=False)
    woo_instance_id = fields.Many2one('woo.instance', ondelete='cascade')
    woo_status = fields.Selection(
        [('pending', 'Pending'),
         ('processing', 'Processing'),
         ('on_hold', 'On-hold'),
         ('completed', 'Completed'),
         ('cancelled', 'Cancelled'),
         ('refunded', 'Refunded'),
         ('failed', 'Failed'),
         ('trash', 'Trash')
         ], string="Woo status")
    woo_order_url = fields.Char(string="Order URL")
    status_woo = fields.Char(string="Status Woo")
    woo_note = fields.Char('Woo Remarks')

    def open_woocommerce_order(self):
        url = self.woo_order_url
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new"
        }

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        if self.woo_id and self.woo_instance_id:
            location = self.woo_instance_id.url
            cons_key = self.woo_instance_id.client_id
            sec_key = self.woo_instance_id.client_secret
            version = 'wc/v3'

            wcapi = API(url=location,
                        consumer_key=cons_key,
                        consumer_secret=sec_key,
                        version=version
                        )
            self.status_woo = 'cancelled'
            data = {
                "status": 'cancelled'
            }
            response = wcapi.put("orders/%s" % self.woo_id, data).json()
        return res

    def update_on_woocommerce(self):
        if self.woo_id and self.woo_instance_id:
            location = self.woo_instance_id.url
            cons_key = self.woo_instance_id.client_id
            sec_key = self.woo_instance_id.client_secret
            version = 'wc/v3'

            wcapi = API(url=location,
                        consumer_key=cons_key,
                        consumer_secret=sec_key,
                        version=version
                        )

            if self.status_woo:
                status = self.status_woo

                data = {
                    "status": status
                }
                response = wcapi.put("orders/%s" % self.woo_id, data).json()
        return

    @api.onchange('order_line')
    def change_price_unit(self):
        if self.order_line:
            for line in self.order_line:
                if line.product_id.woo_id:
                    line.price_unit = line.product_id.woo_sale_price
                else:
                    line.price_unit = line.product_id.lst_price

    def cron_export_sale_order(self):
        all_instances = self.env['woo.instance'].sudo().search([])
        for rec in all_instances:
            if rec:
                self.env['sale.order'].export_selected_so(rec)

    def export_selected_so(self, instance_id):
        location = instance_id.url
        cons_key = instance_id.client_id
        sec_key = instance_id.client_secret
        version = 'wc/v3'

        wcapi = API(url=location,
                    consumer_key=cons_key,
                    consumer_secret=sec_key,
                    version=version
                    )

        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['sale.order'].sudo().browse(selected_ids)
        all_records = self.env['sale.order'].sudo().search([])
        if selected_records:
            records = selected_records
        else:
            records = all_records

        data_list = []
        for rec in records:
            order_lines = []
            for lines in rec.order_line:
                tax_lines = []
                for taxes in lines.tax_id:
                    tax_lines.append({
                        "id": taxes.woo_id if taxes.woo_id else 0,
                    })
                if lines.product_id.woo_id:
                    order_lines.append({
                        "product_id": lines.product_id.woo_id,
                        "quantity": lines.product_uom_qty,
                        "sku": lines.product_id.default_code if lines.product_id.default_code else '',
                        "price": str(lines.price_unit),
                        "total_tax": str(lines.price_tax),
                        "taxes": tax_lines,
                    })
            if rec.partner_id.woo_id:
                list.append({
                    "number": str(rec.name),
                    "id": rec.woo_id,
                    "customer_id": rec.partner_id.woo_id,
                    "currency": rec.currency_id.name,
                    "total_tax": rec.amount_tax,
                    "customer_note": rec.note,
                    "payment_method_title": str(rec.payment_term_id.name) if rec.payment_term_id else '',
                    "billing": {
                        "first_name": rec.partner_id.name if rec.partner_id.name else '',
                        "address_1": rec.partner_id.street if rec.partner_id.street else '',
                        "address_2": rec.partner_id.street2 if rec.partner_id.street2 else '',
                        "city": rec.partner_id.city if rec.partner_id.city else '',
                        "state": rec.partner_id.state_id.name if rec.partner_id.state_id else '',
                        "postcode": rec.partner_id.zip if rec.partner_id.zip else '',
                        "country": rec.partner_id.country_id.name if rec.partner_id.country_id else '',
                        "email": rec.partner_id.email if rec.partner_id.email else "example@gmail.com",
                        "phone": rec.partner_id.phone if rec.partner_id.phone else '',
                    },

                    "shipping": {
                        "first_name": rec.partner_id.name if rec.partner_id.name else '',
                        "address_1": rec.partner_id.street if rec.partner_id.street else '',
                        "address_2": rec.partner_id.street2 if rec.partner_id.street2 else '',
                        "city": rec.partner_id.city if rec.partner_id.city else '',
                        "state": rec.partner_id.state_id.name if rec.partner_id.state_id else '',
                        "postcode": rec.partner_id.zip if rec.partner_id.zip else '',
                        "country": rec.partner_id.country_id.name if rec.partner_id.country_id else '',
                    },
                    "line_items": order_lines,
                })
        if list:
            for data in list:
                if data.get('id'):
                    try:
                        wcapi.post("orders/%s" % (data.get('id')), data).json()
                    except Exception as error:
                        raise UserError(_("Please check your connection and try again"))
                else:
                    try:
                        wcapi.post("orders", data).json()
                    except Exception as error:
                        raise UserError(_("Please check your connection and try again"))
        self.import_sale_order(instance_id)

    def cron_import_sale_order(self):
        all_instances = self.env['woo.instance'].sudo().search([])
        for rec in all_instances:
            if rec:
                self.env['sale.order'].import_sale_order(rec)

    def import_sale_order(self, instance_id):
        page = 1
        while page > 0:
            location = instance_id.url
            cons_key = instance_id.client_id
            sec_key = instance_id.client_secret
            version = 'wc/v3'

            wcapi = API(url=location, consumer_key=cons_key, consumer_secret=sec_key, version=version,timeout=10000,stream=True,chunk_size=1024)
            url = "orders"

            try:
                data = wcapi.get(url, params={'orderby': 'id', 'order': 'desc', 'per_page': 100, 'page': page})
                page += 1
            except Exception as error:
                raise UserError(_("Please check your connection and try again"))

            if data.status_code == 200 and data.content:
                parsed_data = data.json()
                if len(parsed_data) == 0:
                    page = 0
                if parsed_data:
                    for ele in parsed_data:
                        dict_s = {}
                        # searching sales order
                        sale_order = self.env['sale.order'].sudo().search([('woo_id', '=', ele.get('id'))], limit=1)
                        dict_s['woo_instance_id'] = instance_id.id
                        dict_s['is_exported'] = True
                        dict_s['state'] = 'sale'
                        dict_s['company_id'] = instance_id.woo_company_id.id

                        res_partner = ''
                        if not sale_order:
                            dict_s['woo_id'] = ele.get('id')
                            if ele.get('customer_id') == 0 and ele.get('billing') and ele.get('billing').get('email'):
                                email = ele.get('billing').get('email')
                                if email:
                                    res_partner = self.env['res.partner'].sudo().search([('email', '=', email)],
                                                                                        limit=1)
                                    if not res_partner:
                                        dict_a = {}
                                        if ele.get('billing').get('first_name'):
                                            first = ele.get('billing').get('first_name')
                                        else:
                                            first = ""

                                        if ele.get('billing').get('last_name'):
                                            last = ele.get('billing').get('last_name')
                                        else:
                                            last = ""

                                        dict_a['name'] = first + " " + last

                                        if ele.get('billing').get('phone'):
                                            dict_a['phone'] = ele.get('billing').get('phone')
                                        else:
                                            dict_a['phone'] = ''

                                        if ele.get('billing').get('email'):
                                            dict_a['email'] = ele.get('billing').get('email')
                                            if not ele.get('billing').get('first_name') and not ele.get(
                                                    'billing').get(
                                                'last_name'):
                                                dict_a['name'] = ele.get('billing').get('email')
                                        else:
                                            dict_a['email'] = ''

                                        if ele.get('billing').get('postcode'):
                                            dict_a['zip'] = ele.get('billing').get('postcode')
                                        else:
                                            dict_a['zip'] = ''

                                        if ele.get('billing').get('address_1'):
                                            dict_a['street'] = ele.get('billing').get('address_1')
                                        else:
                                            dict_a['street'] = ''

                                        if ele.get('billing').get('address_2'):
                                            dict_a['street2'] = ele.get('billing').get('address_2')
                                        else:
                                            dict_a['street2'] = ''

                                        if ele.get('billing').get('city'):
                                            dict_a['city'] = ele.get('billing').get('city')
                                        else:
                                            dict_a['city'] = ''

                                        if ele.get('billing').get('country'):
                                            country_id = self.env['res.country'].sudo().search(
                                                [('code', '=', ele.get('billing').get('country'))], limit=1)

                                            dict_a['country_id'] = country_id.id

                                            if ele.get('billing').get('state'):
                                                state_id = self.env['res.country.state'].sudo().search(
                                                    ['&', ('code', '=', ele.get('billing').get('state')),
                                                     ('country_id', '=', country_id.id)], limit=1)
                                                if state_id:
                                                    dict_a['state_id'] = state_id.id
                                                else:
                                                    dict_a['state_id'] = False

                                        if dict_a['name'] or dict_a['email']:
                                            res_partner = self.env['res.partner'].sudo().create(dict_a)
                                        else:
                                            res_partner = self.env.user
                                            dict_s['woo_note'] = "No customer from woo commerce"

                            else:
                                res_partner = self.env['res.partner'].sudo().search(
                                    [('woo_id', '=', ele.get('customer_id'))], limit=1)
                            if res_partner:
                                if ele.get('id'):
                                    dict_s['partner_id'] = res_partner.id
                                    dict_s['state'] = 'sale'
                                    dict_s['woo_id'] = ele.get('id')
                                if ele.get('number'):
                                    dict_s['name'] = '#' + str(ele.get('number'))
                                if ele.get('payment_details'):
                                    if ele.get('payment_details').get('method_title'):
                                        pay_id = self.env['account.payment.term']
                                        payment = pay_id.sudo().search([('name', '=', ele.get('payment_details').get('method_title'))], limit=1)
                                        if not payment:
                                            create_payment = payment.sudo().create({
                                                'name': ele.get('payment_details').get('method_title')
                                            })
                                            if create_payment:
                                                dict_s['payment_term_id'] = create_payment.id
                                        else:
                                            dict_s['payment_term_id'] = payment.id
                                if ele.get('total'):
                                    dict_s['amount_total'] = float(ele.get('total'))
                                if ele.get('_links') and ele['_links'].get('customer'):
                                    url = location + 'my-account/view-order/' + '%s' % ele.get('id')
                                    order_url = html_keep_url(url)
                                    woo_order_url = Markup(order_url)
                                    dict_s['woo_order_url'] = url

                                so_obj = self.env['sale.order'].sudo().create(dict_s)

                                for tl in ele.get('tax_lines'):
                                    dict_tax = {}
                                    dict_tax['amount'] = tl.get('rate_percent')
                                    existing_tax = self.env['account.tax'].sudo().search([('woo_id', '=', tl.get('rate_id')),('company_id', '=', instance_id.woo_company_id.id)],limit=1)
                                    if existing_tax:
                                        existing_tax.sudo().write(dict_tax)
                                    else:
                                        dict_tax['woo_instance_id'] = instance_id.id
                                        dict_tax['company_id'] = instance_id.woo_company_id.id
                                        dict_tax['is_exported'] = True
                                        dict_tax['woo_id'] = tl.get('rate_id')
                                        dict_tax['name'] = tl.get('label')
                                        dict_tax['country_id'] = instance_id.woo_company_id.country_id.id
                                        self.env['account.tax'].sudo().create(dict_tax)

                                order_line_list =[]
                                create_invoice = False
                                for i in ele.get('line_items'):
                                    res_product = ''
                                    if i.get('product_id') or i.get('variation_id'):
                                        res_product = self.env['product.product'].sudo().search(
                                            ['|', ('woo_id', '=', i.get('product_id')), ('woo_id', '=', i.get('variation_id'))],
                                            limit=1)
                                        if not res_product:
                                            product = self.env['product.template'].sudo().search(['|', ('woo_id', '=', i.get('product_id')),('woo_id', '=', i.get('variation_id'))], limit=1)
                                            res_product = self.env['product.product'].sudo().create({
                                                'name': i.get('name'),
                                                'detailed_type': 'product',
                                                'woo_sale_price': float(i.get('subtotal')) if i.get('subtotal') != '0.00' else 0,
                                                'lst_price': float(i.get('subtotal')) if i.get('subtotal') != '0.00' else 0,
                                                'product_tmpl_id': product.id if product else '',
                                                'description': product.description_sale if product and product.description_sale else i.get('name'),
                                                'description_sale': product.description_sale if product and product.description_sale else i.get('name'),
                                                'display_name': i.get('name'),
                                                'default_code': i.get('sku'),
                                                'woo_id': i.get('variation_id') if product else i.get('product_id'),
                                            })
                                    if res_product:
                                        dict_l = {}
                                        if i.get('id'):
                                            dict_l['w_id'] = i.get('id')
                                        dict_l['order_id'] = so_obj.id
                                        dict_l['product_id'] = res_product.id
                                        dict_l['name'] = res_product.name

                                        if i.get('quantity'):
                                            dict_l['product_uom_qty'] = i.get('quantity')

                                        if i.get('taxes'):
                                            for t in i.get('taxes'):
                                                existing_tax = self.env['account.tax'].sudo().search([('woo_id', '=', t.get('id'))],limit=1)
                                                if existing_tax:
                                                    dict_l['tax_id'] = [(6, 0, [existing_tax.id])]
                                                else:
                                                    dict_l['tax_id'] = [(6, 0, [])]
                                        else:
                                            dict_l['tax_id'] = [(6, 0, [])]

                                        if i.get('currency'):
                                            cur_id = self.env['res.currency'].sudo().search([('name', '=', 'currency')], limit=1)
                                            dict_l['currency_id'] = cur_id.id

                                        if i.get('subtotal') != '0.00':
                                            dict_l['price_unit'] = float(i.get('subtotal')) / i.get('quantity') if i.get('subtotal') != ' 0.00' and i.get('quantity') else 0.00
                                        else:
                                            dict_l['price_unit'] = 0.00

                                        if i.get('subtotal') != '0.00':
                                            discount_amount = (float(i.get('subtotal'))) - float(i.get('total'))
                                            discount_percentage = (discount_amount / (
                                                float(i.get('subtotal')))) * 100
                                            dict_l['discount'] = discount_percentage
                                        else:
                                            discount_percentage = 0
                                            dict_l['discount'] = discount_percentage

                                        # if i.get('subtotal'):
                                        #     dict_l['price_subtotal'] = float(i.get('subtotal'))

                                        if 'meta_data' in i and i.get('meta_data'):
                                            for record in i.get('meta_data'):
                                                if 'key' in record and record.get('key') == '_vendor_id':
                                                    vendor_id = self.env['res.partner'].sudo().search([('woo_id', '=', record.get('value'))], limit=1)
                                                    dict_l['woo_vendor'] = vendor_id.id


                                        create_p = self.env['sale.order.line'].sudo().create(dict_l)
                                        if create_p.qty_invoiced > 0:
                                            create_invoice = True
                                        order_line_list.append(create_p)

                                if order_line_list:
                                    for sl in ele.get('shipping_lines'):
                                        shipping = self.env['delivery.carrier'].sudo().search([('woo_id', '=', sl.get('method_id'))],limit=1)
                                        if not shipping:
                                            delivery_product = self.env['product.product'].sudo().create({
                                                'name': sl.get('method_title'),
                                                'detailed_type': 'service',
                                            })
                                            vals = {
                                                'woo_id': sl.get('id'),
                                                'is_exported': True,
                                                'woo_instance_id': instance_id.id,
                                                'name': sl.get('method_title'),
                                                'product_id': delivery_product.id,
                                            }
                                            shipping = self.env['delivery.carrier'].sudo().create(vals)
                                        if shipping and shipping.product_id:
                                            shipping_vals = {
                                                'product_id': shipping.product_id.id,
                                                'name':shipping.product_id.name,
                                                'price_unit': float(sl.get('total')),
                                                'order_id': so_obj.id,
                                                'tax_id': [(6, 0, [])]
                                            }
                                            shipping_so_line = self.env['sale.order.line'].sudo().create(shipping_vals)
                                            order_line_list.append(shipping_so_line)

                                if ele.get('payment_method') == 'cod':
                                    so_obj.payment_type = 'cod'
                                else:
                                    so_obj.payment_type = 'prepaid'
                                so_obj.status_woo = ele.get('status')

                                if ele.get('date_paid'):
                                    so_obj.action_confirm()
                                    if create_invoice == True:
                                        # so_obj._prepare_invoice()
                                        so_obj._create_invoices()
                            self.env.cr.commit()

                        else:
                            if sale_order.state != 'done':
                                res_partner = self.env['res.partner'].sudo().search(
                                    [('woo_id', '=', ele.get('customer_id'))], limit=1)
                                if res_partner:
                                    dict_s = {}

                                    if ele.get('id'):
                                        dict_s['partner_id'] = res_partner.id
                                        dict_s['woo_id'] = ele.get('id')
                                        dict_s['state'] = 'draft'

                                    dict_s['status_woo'] = ele.get('status')
                                    # dict_s['woo_status'] = ele.get('status')

                                    if ele.get('number'):
                                        dict_s['name'] = ele.get('number')

                                    if ele.get('payment_details'):
                                        if ele.get('payment_details').get('method_title'):
                                            pay_id = self.env['account.payment.term']
                                            payment = pay_id.sudo().search(
                                                [('name', '=', ele.get('payment_details').get('method_title'))],
                                                limit=1)
                                            if not payment:
                                                create_payment = payment.sudo().create({
                                                    'name': ele.get('payment_details').get('method_title')
                                                })
                                                if create_payment:
                                                    dict_s['payment_term_id'] = create_payment.id
                                            else:
                                                dict_s['payment_term_id'] = payment.id

                                    if ele.get('total'):
                                        dict_s['amount_total'] = ele.get('total')

                                    sale_order.sudo().write(dict_s)
                                    sale_order.status_woo = ele.get('status')

                                    for i in ele.get('line_items'):

                                        res_product = self.env['product.product'].sudo().search(
                                            ['|', ('woo_id', '=', i.get('product_id')),
                                             ('woo_id', '=', i.get('variation_id'))],
                                            limit=1)

                                        if res_product:
                                            s_order_line = self.env['sale.order.line'].sudo().search(
                                                [('product_id', '=', res_product.id),
                                                 (('order_id', '=', sale_order.id))],
                                                limit=1)

                                            if s_order_line:
                                                dict_lp = {}
                                                quantity = 0
                                                ol_qb_id = 0
                                                sp = 0
                                                product_tax_id = 0
                                                if i.get('quantity'):
                                                    quantity = i.get('quantity')

                                                if i.get('id'):
                                                    ol_qb_id = i.get('id')

                                                if i.get('subtotal') != '0.00':
                                                    sp = float(i.get('subtotal')) / i.get('quantity') if i.get(
                                                        'subtotal') != '0.00' and i.get('quantity') else 0.00
                                                else:
                                                    sp = 0.00

                                                if i.get('total_tax'):
                                                    tax = self.env['account.tax']

                                                    if float(i.get('subtotal')):
                                                        total_tax = (float(
                                                            float(i.get('total_tax')) / float(i.get('subtotal'))) * 100)
                                                    else:
                                                        total_tax = 0

                                                    tax_name = "WTax " + '' + str(total_tax) + '%'
                                                    record = tax.sudo().search(
                                                        [('amount', '=', total_tax), ('name', '=', tax_name),
                                                         ('type_tax_use', '=', 'sale')], limit=1)

                                                    _tax_group_id = self.env['account.tax.group'].sudo().search(
                                                        [('name', '=', tax_name)], limit=1)
                                                    if _tax_group_id:
                                                        if not record:
                                                            create_tax = record.sudo().create({
                                                                'amount': total_tax,
                                                                'name': "WTax " + '' + str(total_tax) + '%',
                                                                'amount_type': 'percent',
                                                                'company_id': instance_id.woo_company_id.id,
                                                                'sequence': 1,
                                                                'type_tax_use': 'sale',
                                                                'tax_group_id': _tax_group_id.id,
                                                            })
                                                            if create_tax:
                                                                product_tax_id = [(6, 0, [create_tax.id])]
                                                        else:
                                                            update_tax = record.sudo().write({
                                                                'amount': total_tax,
                                                            })
                                                            if update_tax:
                                                                product_tax_id = [(6, 0, [record.id])]
                                                    else:
                                                        tax_group = _tax_group_id.sudo().create({
                                                            'name': tax_name
                                                        })

                                                        if not record:
                                                            create_tax = record.sudo().create({
                                                                'amount': total_tax,
                                                                'name': "WTax " + '' + str(total_tax) + '%',
                                                                'amount_type': 'percent',
                                                                'company_id': instance_id.woo_company_id.id,
                                                                'sequence': 1,
                                                                'type_tax_use': 'sale',
                                                                'tax_group_id': tax_group.id,
                                                            })
                                                            if create_tax:
                                                                product_tax_id = [(6, 0, [create_tax.id])]
                                                        else:
                                                            update_tax = record.sudo().write({
                                                                'amount': total_tax,
                                                            })
                                                            if update_tax:
                                                                product_tax_id = [(6, 0, [record.id])]
                                                else:
                                                    product_tax_id = [(6, 0, [])]

                                                vendor_id = None
                                                if 'meta_data' in i and i.get('meta_data'):
                                                    for record in i.get('meta_data'):
                                                        if 'key' in record and record.get('key') == '_vendor_id':
                                                            vendor_id = self.env['res.partner'].sudo().search([('woo_id', '=', record.get('value'))], limit=1)

                                                create_po = self.env['sale.order.line'].sudo().search(['&', ('product_id', '=', res_product.id),(('order_id', '=', sale_order.id))], limit=1)
                                                if create_po:
                                                    res = create_po.update({
                                                        'product_id': res_product.id,
                                                        'name': res_product.name,
                                                        'product_uom_qty': quantity,
                                                        'w_id': ol_qb_id,
                                                        'price_unit': sp,
                                                        'tax_id': product_tax_id,
                                                    })
                                            else:
                                                res_product = self.env['product.product'].sudo().search(
                                                    ['|', ('woo_id', '=', i.get('product_id')),
                                                     ('woo_id', '=', i.get('variation_id'))], limit=1)
                                                if res_product:
                                                    dict_l = {}
                                                    if i.get('id'):
                                                        dict_l['w_id'] = i.get('id')

                                                    dict_l['order_id'] = sale_order.id
                                                    dict_l['product_id'] = res_product.id
                                                    dict_l['name'] = res_product.name

                                                    if i.get('quantity'):
                                                        dict_l['product_uom_qty'] = i.get('quantity')

                                                    if i.get('subtotal') != '0.00':
                                                        dict_l['price_unit'] = float(i.get('subtotal')) / i.get(
                                                            'quantity') if i.get('subtotal') != ' 0.00' and i.get(
                                                            'quantity') else 0.00
                                                    else:
                                                        dict_l['price_unit'] = 0.00

                                                    if i.get('total') != '0.00':
                                                        if i.get('subtotal') != ' 0.00':
                                                            discount_amount = (float(i.get('subtotal'))) - float(
                                                                i.get('total'))
                                                            discount_percentage = (discount_amount / (
                                                                float(i.get('subtotal')))) * 100
                                                            dict_l['discount'] = discount_percentage
                                                        else:
                                                            discount_percentage = 0
                                                            dict_l['discount'] = discount_percentage

                                                    if i.get('total_tax'):
                                                        tax = self.env['account.tax']
                                                        if i.get('subtotal') != '0.00':
                                                            total_tax = (float(float(i.get('total_tax')) / float(
                                                                i.get('subtotal'))) * 100)
                                                        else:
                                                            total_tax = 0

                                                        tax_name = "WTax " + '' + str(total_tax) + '%'

                                                        tax = self.env['account.tax']
                                                        record = tax.sudo().search(
                                                            [('amount', '=', total_tax), ('name', '=', tax_name),
                                                             ('type_tax_use', '=', 'sale')], limit=1)
                                                        _tax_group_id = self.env['account.tax.group'].sudo().search(
                                                            [('name', '=', tax_name)], limit=1)
                                                        if _tax_group_id:

                                                            if not record:
                                                                create_tax = record.sudo().create({
                                                                    'amount': total_tax,
                                                                    'name': "WTax " + '' + str(total_tax) + "%",
                                                                    'amount_type': 'percent',
                                                                    'company_id': instance_id.woo_company_id.id,
                                                                    'sequence': 1,
                                                                    'type_tax_use': 'sale',
                                                                    'tax_group_id': _tax_group_id.id,
                                                                })
                                                                if create_tax:
                                                                    dict_l['tax_id'] = [(6, 0, [create_tax.id])]
                                                            else:
                                                                dict_l['tax_id'] = [(6, 0, [record.id])]
                                                        else:
                                                            tax_group = _tax_group_id.sudo().create({
                                                                'name': tax_name
                                                            })
                                                            if not record:
                                                                create_tax = record.sudo().create({
                                                                    'amount': total_tax,
                                                                    'name': "WTax " + '' + str(total_tax) + "%",
                                                                    'amount_type': 'percent',
                                                                    'company_id': instance_id.woo_company_id.id,
                                                                    'sequence': 1,
                                                                    'type_tax_use': 'sale',
                                                                    'tax_group_id': tax_group.id,
                                                                })
                                                                if create_tax:
                                                                    dict_l['tax_id'] = [(6, 0, [create_tax.id])]
                                                            else:
                                                                dict_l['tax_id'] = [(6, 0, [record.id])]

                                                    if i.get('currency'):
                                                        cur_id = self.env['res.currency'].sudo().search([('name', '=', 'currency')], limit=1)
                                                        dict_l['currency_id'] = cur_id.id

                                                    vendor_id = None
                                                    if 'meta_data' in i and i.get('meta_data'):
                                                        for record in i.get('meta_data'):
                                                            if 'key' in record and record.get('key') == '_vendor_id':
                                                                vendor_id = self.env['res.partner'].sudo().search([('woo_id', '=', record.get('value'))], limit=1)
                                                                dict_l['woo_vendor'] = vendor_id.id

                                                    create_p = self.env['sale.order.line'].sudo().create(dict_l)
                                        self.env.cr.commit()
            else:
                page =0

    def woo_order_create(self, data):
        instance_id = self.env['woo.instance'].sudo().search([], limit=1)
        ele = data
        dict_s = {}
        sale_order = self.env['sale.order'].sudo().search(
            [('woo_id', '=', ele.get('id'))], limit=1)
        dict_s['woo_instance_id'] = instance_id.id
        dict_s['is_exported'] = True
        dict_s['state'] = 'sale'
        dict_s['company_id'] = instance_id.woo_company_id.id
        if not sale_order:
            dict_s['woo_id'] = ele.get('id')
            res_partner = self.env['res.partner'].sudo().search(
                [('woo_id', '=', ele.get('customer_id'))], limit=1)
            if res_partner:
                if ele.get('id'):
                    dict_s['partner_id'] = res_partner.id
                    dict_s['state'] = 'sale'
                    dict_s['woo_id'] = ele.get('id')

                if ele.get('number'):
                    dict_s['name'] = '#' + str(ele.get('number'))

                if ele.get('payment_details'):
                    if ele.get('payment_details').get('method_title'):
                        pay_id = self.env['account.payment.term']
                        payment = pay_id.sudo().search(
                            [('name', '=', ele.get('payment_details').get('method_title'))], limit=1)
                        if not payment:
                            create_payment = payment.sudo().create({
                                'name': ele.get('payment_details').get('method_title')
                            })
                            if create_payment:
                                dict_s['payment_term_id'] = create_payment.id
                        else:
                            dict_s['payment_term_id'] = payment.id

                if ele.get('total'):
                    dict_s['amount_total'] = float(ele.get('total'))
                if ele.get('_links') and ele['_links'].get('customer'):
                    url = instance_id.url + 'my-account/view-order/' + '%s' % ele.get('id')
                    order_url = html_keep_url(url)
                    woo_order_url = Markup(order_url)
                    dict_s['note'] = woo_order_url
                so_obj = self.env['sale.order'].sudo().create(dict_s)
                for i in ele.get('line_items'):
                    res_product = self.env['product.product'].sudo().search(
                        ['|', ('woo_id', '=', i.get('product_id')), ('woo_id', '=', i.get('variation_id'))],
                        limit=1)
                    if res_product:
                        dict_l = {}
                        if i.get('id'):
                            dict_l['w_id'] = i.get('id')
                        dict_l['order_id'] = so_obj.id
                        dict_l['product_id'] = res_product.id

                        if i.get('quantity'):
                            dict_l['product_uom_qty'] = i.get('quantity')

                        if i.get('taxes'):
                            for t in i.get('taxes'):
                                existing_tax = self.env['account.tax'].sudo().search(
                                    [('woo_id', '=', t.get('id'))],limit=1)
                                if existing_tax:
                                    dict_l['tax_id'] = [(6, 0, [existing_tax.id])]
                                else:
                                    dict_l['tax_id'] = [(6, 0, [])]
                        else:
                            dict_l['tax_id'] = [(6, 0, [])]

                        if i.get('currency'):
                            cur_id = self.env['res.currency'].sudo().search([('name', '=', 'currency')], limit=1)
                            dict_l['currency_id'] = cur_id.id

                        if i.get('price'):
                            dict_l['price_unit'] = res_product.woo_sale_price

                        # if i.get('subtotal'):
                        #     dict_l['price_subtotal'] = float(i.get('subtotal'))

                        if 'meta_data' in i and i.get('meta_data'):
                            for record in i.get('meta_data'):
                                if 'key' in record and record.get('key') == '_vendor_id':
                                    vendor_id = self.env['res.partner'].sudo().search(
                                        [('woo_id', '=', record.get('value'))], limit=1)
                                    dict_l['woo_vendor'] = vendor_id.id

                        create_p = self.env['sale.order.line'].sudo().create(dict_l)

                for sl in ele.get('shipping_lines'):
                    shipping = self.env['delivery.carrier'].sudo().search([('woo_id', '=', sl.get('method_id'))],limit=1)
                    if shipping and shipping.product_id:
                        shipping_vals = {
                            'product_id': shipping.product_id.id,
                            'price_unit': float(sl.get('total')),
                            'order_id': so_obj.id,
                            'tax_id' : [(6, 0, [])]
                        }
                        shipping_line = self.env['sale.order.line'].sudo().create(shipping_vals)
                if ele.get('payment_method') == 'cod':
                    so_obj.payment_type = 'cod'
                else:
                    so_obj.payment_type = 'prepaid'

                if ele.get('date_paid'):
                    so_obj.action_confirm()
                    so_obj._prepare_invoice()
                    so_obj._create_invoices()

        else:
            if sale_order.state != 'done':
                res_partner = self.env['res.partner'].search([('woo_id', '=', ele.get('customer_id'))], limit=1)
                if res_partner:
                    dict_s = {}

                    if ele.get('id'):
                        dict_s['partner_id'] = res_partner.id
                        dict_s['woo_id'] = ele.get('id')
                        dict_s['state'] = 'draft'

                    if ele.get('number'):
                        dict_s['name'] = ele.get('number')

                    if ele.get('payment_details'):
                        if ele.get('payment_details').get('method_title'):
                            pay_id = self.env['account.payment.term']
                            payment = pay_id.sudo().search(
                                [('name', '=', ele.get('payment_details').get('method_title'))], limit=1)
                            if not payment:
                                create_payment = payment.sudo().create({

                                    'name': ele.get('payment_details').get('method_title')
                                })
                                if create_payment:
                                    dict_s['payment_term_id'] = create_payment.id
                            else:
                                dict_s['payment_term_id'] = payment.id

                    if ele.get('total'):
                        dict_s['amount_total'] = ele.get('total')

                    update_so = self.env['sale.order'].sudo().write(dict_s)

                    for i in ele.get('line_items'):

                        res_product = self.env['product.product'].sudo().search(
                            ['|', ('woo_id', '=', i.get('product_id')), ('woo_id', '=', i.get('variation_id'))],
                            limit=1)

                        if res_product:
                            s_order_line = self.env['sale.order.line'].sudo().search(
                                [('product_id', '=', res_product.id),
                                 (('order_id', '=', sale_order.id))], limit=1)

                            if s_order_line:
                                dict_lp = {}
                                quantity = 0
                                ol_qb_id = 0
                                sp = 0
                                product_tax_id = 0
                                if i.get('quantity'):
                                    quantity = i.get('quantity')

                                if i.get('id'):
                                    ol_qb_id = i.get('id')

                                if i.get('price'):
                                    sp = i.get('price')

                                if i.get('total_tax'):
                                    tax = self.env['account.tax']

                                    if float(i.get('subtotal')):
                                        total_tax = (float(float(i.get('total_tax')) / float(i.get('subtotal'))) * 100)
                                    else:
                                        total_tax = 0

                                    tax_name = "WTax " + '' + str(total_tax) + '%'
                                    record = tax.sudo().search(
                                        [('amount', '=', total_tax), ('name', '=', tax_name),
                                         ('type_tax_use', '=', 'sale')], limit=1)

                                    _tax_group_id = self.env['account.tax.group'].sudo().search(
                                        [('name', '=', tax_name)], limit=1)
                                    if _tax_group_id:

                                        if not record:
                                            create_tax = record.sudo().create({

                                                'amount': total_tax,
                                                'name': "WTax " + '' + str(total_tax) + '%',
                                                'amount_type': 'percent',
                                                'company_id': instance_id.woo_company_id.id,
                                                'sequence': 1,
                                                'type_tax_use': 'sale',
                                                'tax_group_id': _tax_group_id.id,
                                            })
                                            if create_tax:
                                                product_tax_id = [(6, 0, [create_tax.id])]
                                        else:
                                            update_tax = record.sudo().write({
                                                'amount': total_tax,
                                            })
                                            if update_tax:
                                                product_tax_id = [(6, 0, [record.id])]
                                    else:

                                        tax_group = _tax_group_id.sudo().create({
                                            'name': tax_name
                                        })

                                        if not record:
                                            create_tax = record.sudo().create({
                                                'amount': total_tax,
                                                'name': "WTax " + '' + str(total_tax) + '%',
                                                'amount_type': 'percent',
                                                'company_id': instance_id.woo_company_id.id,
                                                'sequence': 1,
                                                'type_tax_use': 'sale',
                                                'tax_group_id': tax_group.id,
                                            })
                                            if create_tax:
                                                product_tax_id = [(6, 0, [create_tax.id])]
                                        else:

                                            update_tax = record.sudo().write({
                                                'amount': total_tax,
                                            })

                                            if update_tax:
                                                product_tax_id = [(6, 0, [record.id])]

                                vendor_id = None
                                if 'meta_data' in i and i.get('meta_data'):
                                    for record in i.get('meta_data'):
                                        if 'key' in record and record.get('key') == '_vendor_id':
                                            vendor_id = self.env['res.partner'].sudo().search(
                                                [('woo_id', '=', record.get('value'))], limit=1)

                                create_po = self.env['sale.order.line'].sudo().search(
                                    ['&', ('product_id', '=', res_product.id),
                                     (('order_id', '=', sale_order.id))], limit=1)

                                if create_po:
                                    res = create_po.update({

                                        'product_id': res_product.id,
                                        'product_uom_qty': quantity,
                                        'w_id': ol_qb_id,
                                        'price_unit': sp,
                                        'tax_id': product_tax_id,
                                    })
                            else:
                                res_product = self.env['product.product'].sudo().search(
                                    ['|', ('woo_id', '=', i.get('product_id')),
                                     ('woo_id', '=', i.get('variation_id'))], limit=1)
                                if res_product:

                                    dict_l = {}
                                    if i.get('id'):
                                        dict_l['w_id'] = i.get('id')

                                    dict_l['order_id'] = sale_order.id

                                    dict_l['product_id'] = res_product.id

                                    if i.get('quantity'):
                                        dict_l['product_uom_qty'] = i.get('quantity')

                                    if i.get('price'):
                                        dict_l['price_unit'] = i.get('price')

                                    if i.get('total_tax'):
                                        total_tax = (float(float(i.get('total_tax')) / float(i.get('subtotal'))) * 100)

                                        tax_name = "WTax " + '' + str(total_tax) + '%'

                                        tax = self.env['account.tax']
                                        record = tax.sudo().search(
                                            [('amount', '=', total_tax), ('name', '=', tax_name),
                                             ('type_tax_use', '=', 'sale')], limit=1)
                                        _tax_group_id = self.env['account.tax.group'].sudo().search(
                                            [('name', '=', tax_name)], limit=1)
                                        if _tax_group_id:
                                            if not record:
                                                create_tax = record.sudo().create({

                                                    'amount': total_tax,
                                                    'name': "WTax " + '' + str(total_tax) + "%",
                                                    'amount_type': 'percent',
                                                    'company_id': instance_id.woo_company_id.id,
                                                    'sequence': 1,
                                                    'type_tax_use': 'sale',
                                                    'tax_group_id': _tax_group_id.id,
                                                })
                                                if create_tax:
                                                    dict_l['tax_id'] = [(6, 0, [create_tax.id])]
                                            else:

                                                dict_l['tax_id'] = [(6, 0, [record.id])]
                                        else:
                                            tax_group = _tax_group_id.sudo().create({
                                                'name': tax_name
                                            })
                                            if not record:

                                                create_tax = record.sudo().create({
                                                    'amount': total_tax,
                                                    'name': "WTax " + '' + str(total_tax) + "%",
                                                    'amount_type': 'percent',
                                                    'company_id': instance_id.woo_company_id.id,
                                                    'sequence': 1,
                                                    'type_tax_use': 'sale',
                                                    'tax_group_id': tax_group.id,
                                                })
                                                if create_tax:
                                                    dict_l['tax_id'] = [(6, 0, [create_tax.id])]
                                            else:

                                                dict_l['tax_id'] = [(6, 0, [record.id])]

                                    if i.get('currency'):
                                        cur_id = self.env['res.currency'].sudo().search(
                                            [('name', '=', 'currency')], limit=1)
                                        dict_l['currency_id'] = cur_id.id

                                    vendor_id = None
                                    if 'meta_data' in i and i.get('meta_data'):
                                        for record in i.get('meta_data'):
                                            if 'key' in record and record.get('key') == '_vendor_id':
                                                vendor_id = self.env['res.partner'].search(
                                                    [('woo_id', '=', record.get('value'))], limit=1)
                                                dict_l['woo_vendor'] = vendor_id.id

                                    create_p = self.env['sale.order.line'].sudo().create(dict_l)
                self.env.cr.commit()
        return


    def woo_order_update(self, data):
        sale_order = self.sudo().search([('woo_id', '=', data.get('id'))], limit=1)
        if sale_order:
            sale_order.status_woo = data.get('status')
        return


class SalerOrderLine(models.Model):
    _inherit = 'sale.order.line'

    w_id = fields.Char('WooCommerce ID')
    woo_vendor = fields.Many2one('res.partner', 'Woo Commerce Vendor')
