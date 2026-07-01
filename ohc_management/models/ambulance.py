from odoo import models, fields,api
from datetime import timedelta



class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    ohc_id = fields.Many2one(
        'ohc.management',
        string='OHC'
    )

    maintenance_start_date = fields.Date(
        string="Maintenance Start Date",
        default=fields.Date.today
    )

    period = fields.Integer(
        string="Preventive Maintenance Frequency",
        help="Number of days"
    )

    next_action_date = fields.Date(
        string="Next Preventive Maintenance",
        compute="_compute_next_action_date",
        store=True
    )

    maintenance_duration = fields.Float(
        string="Maintenance Duration"
    )


    @api.depends(
        'maintenance_start_date',
        'period'
    )
    def _compute_next_action_date(self):
        for rec in self:
            if rec.maintenance_start_date and rec.period:
                rec.next_action_date = (
                    rec.maintenance_start_date +
                    timedelta(days=rec.period)
                )
            else:
                rec.next_action_date = False