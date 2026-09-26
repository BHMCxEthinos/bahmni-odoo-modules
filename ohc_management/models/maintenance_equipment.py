from odoo import models, fields,api
from odoo.exceptions import ValidationError

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

    # --- Next Calibration Date ---

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

    @api.depends(
    'calibration_log_ids.next_due',
    'calibration_log_ids.cal_date'
)
    def _compute_next_calibration_date(self):
        for equipment in self:
            calibration_logs = equipment.calibration_log_ids.filtered(
                lambda log: log.cal_date
            )

            if calibration_logs:
                latest_log = calibration_logs.sorted(
                    key=lambda log: log.cal_date,
                    reverse=True
                )[0]

                equipment.next_calibration_date = latest_log.next_due
            else:
                equipment.next_calibration_date = False


class CalibrationLog(models.Model):
    _inherit = 'servia.calibration.log'
    _description = 'Calibration Log'


    @api.constrains('equipment_id', 'cal_date')
    def _check_duplicate_calibration_date(self):
        for record in self:
            if not record.equipment_id or not record.cal_date:
                continue

            duplicate = self.search([
                ('id', '!=', record.id),
                ('equipment_id', '=', record.equipment_id.id),
                ('cal_date', '=', record.cal_date),
            ], limit=1)

            if duplicate:
                raise ValidationError(
                    "A calibration record already exists for equipment "
                    "'%s' on %s.\n\n"
                    "Two calibration records cannot have the same "
                    "Calibration Date for the same equipment."
                    % (
                        record.equipment_id.display_name,
                        record.cal_date.strftime('%d/%m/%Y'),
                    )
                )

    


    