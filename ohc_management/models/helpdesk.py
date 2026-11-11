from odoo import models, fields

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    ohc_id = fields.Many2one(
        'ohc.management',
        string='OHC'
    )