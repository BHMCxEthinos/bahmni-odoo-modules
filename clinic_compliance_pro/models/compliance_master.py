from odoo import models, fields

class ComplianceMaster(models.Model):
    _name = 'clinic.compliance.master'
    _description = 'Compliance Master'

    name = fields.Char(string='Name', required=True)
    category = fields.Selection([
    ('safety', 'Safety'),
    ('medical', 'Medical'),
    ('legal', 'Legal'),
    ('environmental', 'Environmental'),
    ('other', 'Other'),
], string='Category', default='other')
    period_days = fields.Integer(string='Re-check Period (Days)')
