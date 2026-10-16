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
            string='Technician',
            domain=[('is_company', '=', False)],    
        )
    
    partner_id = fields.Many2one(
            'res.partner',
            string='Vendor',
            domain=[('is_company', '=', True)],
        )

    calibration_log_ids = fields.One2many(
            'servia.calibration.log',
            'equipment_id',
            string="Calibration Logs"
        )
    
    next_calibration_date = fields.Date(
            string="Next Calibration Date",
            compute="_compute_next_calibration_date",
            store=True,
        )
    
    @api.depends('calibration_log_ids.next_due', 'calibration_log_ids.cal_date')
    def _compute_next_calibration_date(self):
        for equipment in self:
                    # sort by next_due ascending, take the earliest one
            logs_with_due = equipment.calibration_log_ids.filtered('next_due')
            earliest_log = logs_with_due.sorted('next_due')[:1]  # ascending, no reverse
            equipment.next_calibration_date = earliest_log.next_due if earliest_log else False
    