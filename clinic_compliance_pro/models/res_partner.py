from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_ohc = fields.Boolean(string='Is OHC', default=False)
    compliance_ids = fields.One2many(
        'clinic.compliance.record', 'clinic_id', string='Compliance Records')
    compliance_count = fields.Integer(
        string='Compliance Count',
        compute='_compute_compliance_count',
        store=True)
    compliance_status = fields.Selection([
        ('green', 'All Valid'),
        ('orange', 'Some Expiring'),
        ('red', 'Some Expired'),
        ('none', 'No Records'),
    ], string='Compliance Status',
        compute='_compute_compliance_status',
        store=True)

    @api.depends('compliance_ids')
    def _compute_compliance_count(self):
        for rec in self:
            rec.compliance_count = len(rec.compliance_ids)

    @api.depends('compliance_ids.status')
    def _compute_compliance_status(self):
        for rec in self:
            statuses = rec.compliance_ids.mapped('status')
            if not statuses:
                rec.compliance_status = 'none'
            elif 'red' in statuses:
                rec.compliance_status = 'red'
            elif 'orange' in statuses:
                rec.compliance_status = 'orange'
            else:
                rec.compliance_status = 'green'

    def action_view_compliance(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Compliance Records',
            'res_model': 'clinic.compliance.record',
            'view_mode': 'tree,form',
            'domain': [('clinic_id', '=', self.id)],
            'context': {'default_clinic_id': self.id},
        }