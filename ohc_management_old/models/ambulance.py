from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    ohc_id = fields.Many2one(
        'ohc.management',
        string='OHC'
    )

    ohc_purchase_date = fields.Date(
        string='Vehicle Purchase Date',
        required=True,
    )

    ohc_last_maintenance_date = fields.Date(
        string='Last Maintenance Date',
        required=True,
    )

    maintenance_start_date = fields.Date(
        string="Maintenance Start Date",
        default=fields.Date.today
    )

    period = fields.Integer(
        string="Preventive Maintenance Frequency",
        help="Number of days",
        required=True,
    )

    next_action_date = fields.Date(
        string="Next Preventive Maintenance",
        compute="_compute_next_action_date",
        store=True
    )

    maintenance_duration = fields.Float(
        string="Maintenance Duration"
    )

    ohc_insurance_expiry_date = fields.Date(
        string='Insurance Expiry Date',
    )

    ohc_puc_validity_date = fields.Date(
        string='PUC Validity Date',
    )

    ohc_ambulance_movement = fields.Selection([
        ('with_patient', 'With Patient'),
        ('without_patient', 'Without Patient'),
    ], string='Ambulance Movement')

    ohc_movement_date = fields.Date(
        string='Ambulance Movement Date',
    )

    ohc_movement_time = fields.Float(
        string='Ambulance Movement Time',
    )

    ohc_departure_time = fields.Float(
        string='Departure Time',
    )

    ohc_departure_start_km = fields.Float(
        string='Departure Start Km',
    )

    ohc_patient_name = fields.Char(
        string='Patient Name',
    )

    ohc_purpose = fields.Selection([
        ('service_to_patient', 'Service to Patient'),
        ('petrol_pump', 'Petrol Pump'),
        ('vehicle_service', 'Vehicle Service'),
    ], string='Purpose')

    ohc_destination = fields.Char(
        string='Destination',
    )

    ohc_arrival_time = fields.Float(
        string='Arrival Time',
    )

    ohc_arrival_end_km = fields.Float(
        string='Arrival End Km',
    )

    ohc_distance_travelled = fields.Float(
        string='Distance Travelled',
        compute='_compute_distance',
        store=True,
    )

    ohc_notes = fields.Text(
        string='Notes',
    )

    ohc_driver_name = fields.Char(
        string='Driver Name',
    )

    @api.depends('ohc_last_maintenance_date', 'period')
    def _compute_next_action_date(self):
        for rec in self:
            if rec.ohc_last_maintenance_date and rec.period:
                rec.next_action_date = (
                    rec.ohc_last_maintenance_date +
                    timedelta(days=rec.period)
                )
            else:
                rec.next_action_date = False

    @api.onchange('ohc_purchase_date')
    def _onchange_ohc_purchase_date(self):
        for rec in self:
            if rec.ohc_purchase_date and not rec.ohc_last_maintenance_date:
                rec.ohc_last_maintenance_date = rec.ohc_purchase_date

    @api.depends('ohc_departure_start_km', 'ohc_arrival_end_km')
    def _compute_distance(self):
        for rec in self:
            rec.ohc_distance_travelled = (
                rec.ohc_arrival_end_km - rec.ohc_departure_start_km
            )

    @api.constrains('co2')
    def _check_co2_emissions(self):
        for rec in self:
            if rec.co2 < 0:
                raise ValidationError('CO2 Emissions cannot be a negative value.')

    @api.constrains('driver_id', 'future_driver_id', 'manager_id')
    def _check_unique_driver_manager(self):
        for rec in self:
            values = [rec.driver_id.id, rec.future_driver_id.id, rec.manager_id.id]
            values = [v for v in values if v]
            if len(values) != len(set(values)):
                raise ValidationError(
                    _('Driver, Future Driver, and Fleet Manager must all be different people.')
                )

    class FleetVehicleModel(models.Model):
        _inherit = 'fleet.vehicle.model'

        def _get_vehicle_type_selection(self):
            return [('car', 'Ambulance')]

        vehicle_type = fields.Selection(
            selection='_get_vehicle_type_selection',
            string='Vehicle Type',
            default='car',
            required=True,
        )

class FleetVehicleOdometer(models.Model):
    _inherit = 'fleet.vehicle.odometer'

    ohc_ambulance_movement = fields.Selection([
        ('with_patient', 'With Patient'),
        ('without_patient', 'Without Patient'),
    ], string='Ambulance Movement')
    ohc_movement_date = fields.Date(string='Ambulance Movement Date')
    ohc_movement_time = fields.Float(string='Ambulance Movement Time')
    ohc_departure_time = fields.Float(string='Departure Time')
    ohc_departure_start_km = fields.Float(string='Departure Start Km')
    ohc_patient_name = fields.Char(string='Patient Name')
    ohc_purpose = fields.Selection([
        ('service_to_patient', 'Service to Patient'),
        ('petrol_pump', 'Petrol Pump'),
        ('vehicle_service', 'Vehicle Service'),
    ], string='Purpose')
    ohc_destination = fields.Char(string='Destination')
    ohc_arrival_time = fields.Float(string='Arrival Time')
    ohc_arrival_end_km = fields.Float(string='Arrival End Km')
    ohc_distance_travelled = fields.Float(
        string='Distance Travelled',
        compute='_compute_distance_odometer',
        store=True,
    )
    ohc_notes = fields.Text(string='Notes')
    ohc_driver_name = fields.Char(string='Driver Name')

    @api.depends('ohc_departure_start_km', 'ohc_arrival_end_km')
    def _compute_distance_odometer(self):
        for rec in self:
            rec.ohc_distance_travelled = (
                rec.ohc_arrival_end_km - rec.ohc_departure_start_km
            )

    @api.onchange('ohc_ambulance_movement')
    def _onchange_ohc_ambulance_movement(self):
        if self.ohc_ambulance_movement == 'without_patient':
            self.ohc_patient_name = False

class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    vendor_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        domain="[('is_company', '=', True)]",
    )