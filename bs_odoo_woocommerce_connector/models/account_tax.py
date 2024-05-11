# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountTax(models.Model):
    _inherit = 'account.tax'

    woo_tax_id = fields.Integer('Woo Tax Id')

    @staticmethod
    def woo_tax_to_odoo(datas):
        return {
            'name': datas.get('name'),
            'amount': datas.get('rate'),
            'woo_tax_id': datas.get('id')
        }

    def _get_create_tax_grp(self):
        woo_tax = self.env['account.tax.group'].search_read([('name', '=', 'Woo Taxes')], ['id'])
        if not len(woo_tax):
            tax_grp = self.env['account.tax.group'].create({
                'name': 'Woo Taxes'
            })
            return tax_grp.id
        return woo_tax[0]['id']

    def get_tax_batch(self, wcapi, instance):
        log_obj = self.env['synchronization.log']
        try:
            failed_ids = []
            response = wcapi.get('taxes')
            if response.status_code == 200:
                datas = response.json()
                for data in datas:
                    tax = self._create_taxes(data=data)
                    if not tax:
                        failed_ids.append(data.get('id'))
            log_obj.sudo().create({
                'operation_type': 'import',
                'operation_on': 'tax',
                'status_code': response.status_code,
                'method': response.request.method,
                'url': response.url,
                'model': self._name,
                'message': response.text,
                'failed_ids': failed_ids or '',
                'company_id': instance.company_id.id
            })
        except Exception as e:
            log_obj.sudo().create({
                'operation_type': 'import',
                'status_code': '',
                'method': '',
                'url': '',
                'model': self._name,
                'message': str(e),
                'company_id': instance.company_id.id
            })

    def _create_taxes(self, data):
        existing_tax = self.search_read([('woo_tax_id', '=', data.get('id'))])
        if not existing_tax:
            vals = self.woo_tax_to_odoo(data)
            country_iso = data.get('country')
            country = self.env['res.country'].search([('code', '=', country_iso)])
            if country:
                vals['country_id'] = country.id
            vals['tax_group_id'] = self._get_create_tax_grp()
            return self.create(vals)
        return existing_tax

    def _get_tax_ids(self, taxes):
        tax_ids = []
        for tax_data in taxes:
            tax = self.search_read([('woo_tax_id', '=', tax_data.get('id'))])
            if tax:
                tax_ids.append(tax[0]['id'])
        return tax_ids
