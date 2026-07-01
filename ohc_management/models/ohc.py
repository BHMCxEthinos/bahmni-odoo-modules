# -*- coding: utf-8 -*-

from odoo import models, fields,api,_
import logging
_logger = logging.getLogger(__name__)


class OhcManagement(models.Model):
    _name = 'ohc.management'
    _description = 'OHC Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    # Basic Information

    name = fields.Char(
        string='OHC Name',
        required=True,
        tracking=True
    )

    state = fields.Selection([
        ('onboarding', 'ONBOARDING'),
        ('setup', 'SETUP'),
        ('audit', 'IN AUDIT'),
        ('active', 'ACTIVE'),
        ('closed', 'CLOSED'),
    ],
        string='Status',
        default='onboarding',
        tracking=True
    )

 
    company_id = fields.Many2one(
        'res.partner',
        string='Customer',
        tracking=True
    )

    

    street = fields.Char(string='Street')

    street2 = fields.Char(string='Street 2')

    city = fields.Char(
        string='Village / City'
    )

    sub_district = fields.Char(
        string='Sub-District'
    )

    district = fields.Char(
        string='District'
    )

    state_id = fields.Many2one(
    'res.country.state',
    string='State',
    domain="[('country_id', '=', country_id)]"
)

   

    zip = fields.Char(
        string='ZIP'
    )

    country_id = fields.Many2one(
        'res.country',
        string='Country'
    )

    # OHC Information

    # ohc_id = fields.Char(
    #     string='OHC ID'
    # )
    ohc_id = fields.Char(
        string='OHC ID',
        readonly=True,
        copy=False,
        default=lambda self: _('New')
    )

    @api.model
    def create(self, vals):
        if vals.get('ohc_id', _('New')) == _('New'):
            vals['ohc_id'] = self.env['ir.sequence'].next_by_code(
                'ohc.management'
            ) or _('New')

        return super().create(vals)

    abdm_facility_id = fields.Char(
        string='ABDM Facility ID'
    )

    operation_manager = fields.Many2one(
        'hr.employee',
        string='Operation Manager'
    )

    # Contact Information

    hr_contact_name = fields.Char(
        string='HR Contact Name'
    )

    phone = fields.Char(
        string='Phone'
    )

    mobile = fields.Char(
        string='Mobile'
    )

    email = fields.Char(
        string='Email'
    )

    website = fields.Char(
        string='Website'
    )

    tags = fields.Char(
        string='Tags'
    )

    # Project Details

    onboarding_project = fields.Many2one(
        'project.project',
        string='Onboarding Project',
        readonly=True
    )

    project_status = fields.Selection([
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('off_track', 'Off Track'),
        ('on_hold', 'On Hold'),
    ],
        string='Project Status',
        readonly=True
    )

   

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse'
    )

    additional_notes = fields.Text(
    string='Additional Notes'
)

    def update_project_details(self, project=False):

        for rec in self:

            if not project:

                project = self.env['project.project'].search(
                    [('ohc_id', '=', rec.id)],
                    limit=1
                )

            rec.onboarding_project = project.id if project else False

            rec.project_status = False

            if project:

                latest_update = self.env['project.update'].search(
                    [('project_id', '=', project.id)],
                    order='id desc',
                    limit=1
                )

                if latest_update:
                    rec.project_status = latest_update.status

    # Smart Button Counts

    checklist_count = fields.Integer(
        string='Checklist Count',
        default=0
    )

    stock_count = fields.Integer(
        string='Stock Count',
        default=0
    )

    ambulance_log_count = fields.Integer(
        string='Ambulance Log',
        default=0
    )

    helpdesk_ticket_count = fields.Integer(
        string='Helpdesk Tickets',
        default=0
    )

    document_count = fields.Integer(
        string='Documents',
        default=0
    )

    employee_ids = fields.One2many(
    'hr.employee',
    'ohc_id',
    string='Staff'
)
    
    equipment_ids = fields.One2many(
        'maintenance.equipment',
        'ohc_id',
        string='Equipments'
    )
    
    vehicle_ids = fields.One2many(
    'fleet.vehicle',
    'ohc_id',
    string='Ambulances'
)
    stock_line_ids = fields.One2many(
    'ohc.stock.line',
    'ohc_id',
    string='Stock In Hand'
)
    def action_load_stock(self):
        StockLine = self.env['ohc.stock.line']
        Quant = self.env['stock.quant']

        for rec in self:

            # Remove old records
            rec.stock_line_ids.unlink()

            if not rec.warehouse_id:
                continue

            # Get warehouse root location
            warehouse_location = rec.warehouse_id.view_location_id

            # All child locations
            locations = self.env['stock.location'].search([
                ('id', 'child_of', warehouse_location.id),
                ('usage', '=', 'internal')
            ])

            quants = Quant.search([
                ('location_id', 'in', locations.ids),
                ('quantity', '>', 0)
            ])

            vals_list = []

            for quant in quants:

                vals_list.append({
                    'ohc_id': rec.id,
                    'product_id': quant.product_id.id,
                    'location_id': quant.location_id.id,
                    'lot_id': quant.lot_id.id if quant.lot_id else False,
                    'available_qty': quant.available_quantity,
                    'quantity': quant.quantity,
                    'removal_date': quant.lot_id.removal_date if quant.lot_id else False,
                    'uom_id': quant.product_id.uom_id.id,
                })

        StockLine.create(vals_list)

    service_type = fields.Selection([
        ('24x7', '24x7'),
        ('12hr', '12 Hours'),
        ('general', 'General')
    ], string="Operations")


    ambulance_count = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
    ], string="Ambulance")


    doctor_count = fields.Selection([
        ('0','0'),
        ('1','1'),
        ('2','2'),
        ('3','3'),
        ('4','4'),
        ('5','5'),
    ], string="Doctors")


    nurse_count = fields.Selection([
        ('0','0'),
        ('1','1'),
        ('2','2'),
        ('3','3'),
        ('4','4'),
        ('5','5'),
    ], string="Nurses")


    driver_count = fields.Selection([
        ('0','0'),
        ('1','1'),
        ('2','2'),
        ('3','3'),
    ], string="Drivers")


    bp_machine_count = fields.Integer(string="BP Machine")


    ecg_machine_count = fields.Integer(string="ECG Machine")


    aed_machine_count = fields.Integer(string="AED Machine")


    pulsox_count = fields.Integer(string="Pulsox")


    o2_kit_count = fields.Integer(string="O2 Kit")


    other_services = fields.Text(
        string="Other"
    )

    # Smart Button Actions

    # def action_open_checklist(self):
    #     return True
    def action_open_checklist(self):

        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Survey',
            'res_model': 'survey.selection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ohc_id': self.id,
            }
        }
    
    last_checklist_date = fields.Char(
    string="Last Checklist Filled",
    compute="_compute_last_checklist_date"
)


    checklist_count = fields.Integer(
        compute="_compute_last_checklist_date"
    )



    def _compute_last_checklist_date(self):
        SurveyInput = self.env['survey.user_input']

        for rec in self:
            answer = SurveyInput.search(
                [
                    ('ohc_id', '=', rec.id),
                    ('state', '=', 'done')
                ],
                order='write_date desc',
                limit=1
            )

            if answer:
                dt = fields.Datetime.context_timestamp(rec, answer.write_date)
                rec.last_checklist_date = dt.strftime("%d/%m/%Y\n%I:%M:%S %p")
            else:
                rec.last_checklist_date = "No Checklist"

            rec.checklist_count = SurveyInput.search_count([
                ('ohc_id', '=', rec.id),
                ('state', '=', 'done')
            ])

    def action_open_stock(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Transfers',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [
                '|',
                ('location_id', 'child_of', self.warehouse_id.view_location_id.id),
                ('location_dest_id', 'child_of', self.warehouse_id.view_location_id.id),
            ],
            'context': {
                'ohc_mode': True,
                'ohc_warehouse_id': self.warehouse_id.id,
                'ohc_root_location_id': self.warehouse_id.view_location_id.id,
            },
        }

    def action_open_ambulance_log(self):
        self.ensure_one()

        vehicle_ids = self.env['fleet.vehicle'].search([
            ('ohc_id', '=', self.id)
        ]).ids

        return {
            'type': 'ir.actions.act_window',
            'name': 'Ambulance Logs',
            'res_model': 'fleet.vehicle.odometer',
            'view_mode': 'tree,form',
            'domain': [('vehicle_id', 'in', vehicle_ids)],
            'context': {
                'search_default_group_vehicle_id': 1,
            }
        }

    def action_open_helpdesk(self):

        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Helpdesk Tickets',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form',
            'domain': [
                ('ohc_id', '=', self.id),
                ('state', 'not in', [
                    'resolved',
                    'closed',
                    'cancelled'
                ])
            ],
            'context': {
                'default_ohc_id': self.id,
            },
        }
    

    # def action_open_documents(self):
    #     return True
    def action_open_documents(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Compliance Records',
            'res_model': 'clinic.compliance.record',
            'view_mode': 'tree,form',
            'domain': [
                ('clinic_id', '=', self.id)
            ],
            'context': {
                'default_ohc_id': self.id,
            }
        }
    
    compliance_document_count = fields.Integer(
    string='Compliance Documents',
    compute='_compute_compliance_document_count'
)

    def _compute_compliance_document_count(self):
        Compliance = self.env['clinic.compliance.record']

        for rec in self:
            compliances = Compliance.search([
                ('clinic_id', '=', rec.id)
            ])

            rec.compliance_document_count = sum(
                len(compliance.document_ids)
                for compliance in compliances
            )
            
    helpdesk_ticket_count = fields.Integer(
    compute='_compute_helpdesk_ticket_count'
)
    def _compute_helpdesk_ticket_count(self):
        for rec in self:

            rec.helpdesk_ticket_count = self.env[
                'helpdesk.ticket'
            ].search_count([
                ('ohc_id', '=', rec.id),
                ('state', 'not in', [
                    'resolved',
                    'closed',
                    'cancelled'
                ])
            ])

    # Warehouse short code 
    @api.model
    def create(self, vals):

        if vals.get('ohc_id', 'New') == 'New':
            vals['ohc_id'] = self.env['ir.sequence'].next_by_code(
                'ohc.management'
            ) or 'New'

        record = super().create(vals)

        if record.warehouse_id:
            record.warehouse_id.code = record.ohc_id

        return record
    
    def write(self, vals):
        res = super().write(vals)

        for rec in self:
            if rec.warehouse_id and rec.ohc_id:
                rec.warehouse_id.code = rec.ohc_id

        return res

   
        
   


# =========================================================
# STAFF LINE MODEL
# =========================================================

class OhcStaffLine(models.Model):
    _name = 'ohc.staff.line'
    _description = 'OHC Staff Line'

    # ohc_id = fields.Manye2one(
    #     'ohc.management',
    #     string='OHC'
    # )
    ohc_id = fields.Many2one(
        'ohc.management',
        string='OHC',
        required=True
    )

    _sql_constraints = [
        (
            'unique_ohc',
            'unique(ohc_id)',
            'Only one staff record can be linked to one OHC.'
        )
    ]

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True
    )

    designation = fields.Char(
        string='Role/Designation',
        related='employee_id.job_id.name',
        store=True
    )

    mobile = fields.Char(
        string='Mobile',
        related='employee_id.mobile_phone',
        store=True
    )

    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], default='active')

    shift = fields.Selection([
        ('first', 'First'),
        ('second', 'Second'),
        ('third', 'Third')
    ], string='Shift')



class OhcStockLine(models.Model):
    _name = 'ohc.stock.line'
    _description = 'OHC Stock In Hand'

    ohc_id = fields.Many2one(
        'ohc.management',
        string='OHC',
        ondelete='cascade'
    )

    product_id = fields.Many2one(
        'product.product',
        string='Product'
    )

    location_id = fields.Many2one(
        'stock.location',
        string='Location'
    )

    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot/Serial Number'
    )

    available_qty = fields.Float(
        string='Available Quantity'
    )

    quantity = fields.Float(
        string='On Hand Quantity'
    )

    removal_date = fields.Datetime(
        string='Removal Date'
    )

    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure'
    )


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.onchange('picking_type_id')
    def _onchange_filter_locations(self):

        root_location_id = self.env.context.get('ohc_root_location_id')

        if root_location_id:
            return {
                'domain': {
                    'location_id': [
                        ('location_id', '=', root_location_id),
                        ('usage', '=', 'internal')
                    ],
                    'location_dest_id': [
                        ('location_id', '=', root_location_id),
                        ('usage', '=', 'internal')
                    ],
                }
            }

    ohc_warehouse_id = fields.Many2one(
        'stock.warehouse',
        default=lambda self: self.env.context.get('ohc_warehouse_id')
    )

    