from odoo import models, fields

class ComplianceDocument(models.Model):
    _name = 'clinic.compliance.document'
    _description = 'Compliance Document'

    name = fields.Char(string='Document Name', required=True)
    record_id = fields.Many2one('clinic.compliance.record', string='Record')
