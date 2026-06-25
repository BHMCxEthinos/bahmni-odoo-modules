from odoo import models, fields

class ComplianceTemplate(models.Model):
    _name = 'clinic.compliance.template'
    _description = 'Compliance Template'

    name = fields.Char(string='Template Name', required=True)
    compliance_ids = fields.Many2many(
        'clinic.compliance.master',
        'compliance_template_master_rel',
        'template_id',
        'master_id',
        string='Compliances')