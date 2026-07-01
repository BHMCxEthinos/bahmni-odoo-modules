from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    ohc_id = fields.Many2many(
        'ohc.management',
        string='OHC'
    )

    employee_status = fields.Selection([
    ('active', 'Active'),
    ('inactive', 'In Active'),
], string='Employee Status', default='active')