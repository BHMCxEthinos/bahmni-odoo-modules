from odoo import models, fields, api

class ComplianceWizard(models.TransientModel):
    _name = 'clinic.compliance.wizard'
    _description = 'Create Compliance from Template'

    ohc_id = fields.Many2one(
        'ohc.management',
        string='OHC',
        required=True)
    template_id = fields.Many2one(
        'clinic.compliance.template',
        string='Template',
        required=True)

    def action_create_records(self):
        for compliance in self.template_id.compliance_ids:
            self.env['clinic.compliance.record'].create({
                'clinic_id': self.ohc_id.id,
                'master_id': compliance.id,
                'status': 'green',
                'expiry_date': False,
            })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Compliance Records',
            'res_model': 'clinic.compliance.record',
            'view_mode': 'tree,form',
            'domain': [('clinic_id', '=', self.ohc_id.id)],
        }