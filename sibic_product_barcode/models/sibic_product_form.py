# -*- coding: utf-8 -*-

import math
import re
from odoo import api, models


class SibicProductAutoBarcode(models.Model):
    _inherit = 'product.product'

    
    @api.model
    def create(self, vals_list):
        templates = super(SibicProductAutoBarcode, self).create(vals_list)
        if  templates.barcode == False :
            ean = generate_ean('20A'+str(templates.id))
            templates.barcode = ean
        return templates

    @api.model
    def write(self, vals_list):
        templates = super(SibicProductAutoBarcode, self).write(vals_list)
        if vals_list.get('barcode')== False:
             self.barcode = generate_ean('20A'+str(self.id))
        return templates


def ean_checksum(eancode):
    """returns the checksum of an ean string of length 13, returns -1 if
    the string has the wrong length"""
    if len(eancode) != 13:
        return -1
    oddsum = 0
    evensum = 0
    eanvalue = eancode
    reversevalue = eanvalue[::-1]
    finalean = reversevalue[1:]

    for i in range(len(finalean)):
        if i % 2 == 0:
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total = (oddsum * 3) + evensum

    check = int(10 - math.ceil(total % 10.0)) % 10
    return check


def check_ean(eancode):
    """returns True if eancode is a valid ean13 string, or null"""
    if not eancode:
        return True
    if len(eancode) != 13:
        return False
    try:
        int(eancode)
    except:
        return False
    return ean_checksum(eancode) == int(eancode[-1])


def generate_ean(ean):
    """Creates and returns a valid ean13 from an invalid one"""
    if not ean:
        return "0000000000000"
    ean = re.sub("[A-Za-z]", "0", ean)
    ean = re.sub("[^0-9]", "", ean)
    ean = ean[:13]
    if len(ean) < 13:
        ean = ean + '1'+'0' * (12 - len(ean))
    return ean[:-1] + str(ean_checksum(ean))


class SibicProductTemplateAutoBarcode(models.Model):
    _inherit = 'product.template'
   
    @api.model
    def create(self, vals_list):
        templates = super(SibicProductTemplateAutoBarcode, self).create(vals_list)
        if  templates.barcode == False :
            ean = generate_ean('20'+str(templates.id))
            templates.barcode = ean
        return templates

    @api.model
    def write(self, vals_list):
        templates = super(SibicProductTemplateAutoBarcode, self).write(vals_list)
        if vals_list.get('barcode')== False:
             self.barcode = generate_ean('20'+str(self.id))
        return templates


