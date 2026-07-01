from odoo import models, fields,api


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    ohc_id = fields.Many2one(
        'ohc.management',
        string='OHC'
    )


    location = fields.Selection([
        ('clinic', 'Clinic'),
        ('ambulance', 'Ambulance'),
    ], string="Used in location")

    amc_contact = fields.Char(
        string='AMC Contact',
        compute='_compute_amc_contact',
        store=True
    )

    @api.depends('technician_partner_id.phone', 'technician_partner_id.mobile')
    def _compute_amc_contact(self):
        for rec in self:
            rec.amc_contact = (
                rec.technician_partner_id.phone
                or rec.technician_partner_id.mobile
                or False
            )



    technician_partner_id = fields.Many2one(
        'res.partner',
        string='Technician'
    )

