from datetime import datetime, date, timedelta
from odoo import models, fields, api


class EgSyncHistory(models.Model):
    _inherit = "eg.sync.history"
