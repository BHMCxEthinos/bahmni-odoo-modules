from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    message_main_attachment_id = fields.Many2one(
            groups='hr.group_hr_user,ohc_management.group_ohc_employee_readonly'
        )
    
    ohc_id = fields.Many2many(
        'ohc.management',
        string='OHC'
    )

    employee_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'In Active'),
    ], string='Employee Status', default='active')


    def write(self, vals):
        res = super(HrEmployee, self).write(vals)

        # If OHC assignment changes, clear record rule cache
        if 'ohc_id' in vals:
            self.env['ir.rule'].clear_caches()

        return res

    # -- Employee ID --
    ohc_employee_id = fields.Char(
        string='Employee ID',
        copy=False,
        tracking=True,
        required=True,
    )

    # -- Joining Date --
    ohc_joining_date = fields.Date(
        string='Joining Date',
    )

    # -- Compliance/Training Status --
    ohc_compliance_status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('not_done', 'Not Done'),
        ('na', 'NA'),
    ], string='Compliance/Training Status')

    # -- Work Experience --
    ohc_work_experience = fields.Float(
        string='Work Experience (Years)',
        digits=(5, 1),
    )

    # -- Driving Licence --
    ohc_driving_licence = fields.Char(
        string='Driving Licence',
    )

    # -- Commercial Licence --
    ohc_commercial_licence = fields.Char(
        string='Commercial Licence',
    )

    # -- PF Number --
    ohc_pf_number = fields.Char(
        string='PF',
    )

    # -- ESI Number --
    ohc_esi_number = fields.Char(
        string='ESI',
    )

    # -- Locum / Backup Staff --
    ohc_locum_id = fields.Many2one(
        'hr.employee',
        string='Locum/Backup Staff',
    )

    ohc_leaving_date = fields.Date(
        string='Leaving Date',
    )

    @api.constrains('ohc_joining_date', 'ohc_leaving_date')
    def _check_leaving_date(self):
        for rec in self:
            if rec.ohc_joining_date and rec.ohc_leaving_date:
                if rec.ohc_leaving_date < rec.ohc_joining_date:
                    raise ValidationError(
                        _('Leaving Date cannot be before Joining Date.')
                    )


    @api.constrains('ohc_employee_id')
    def _check_unique_employee_id(self):
        for rec in self:
            if rec.ohc_employee_id:
                duplicate = self.search([
                    ('ohc_employee_id', '=', rec.ohc_employee_id),
                    ('id', '!=', rec.id),
                ])
                if duplicate:
                    raise ValidationError(
                        _('Employee ID "%s" is already assigned to "%s". '
                          'Please use a unique Employee ID.')
                        % (rec.ohc_employee_id, duplicate[0].name)
                    )

class HrPlan(models.Model):
    _inherit = 'hr.plan'

    _sql_constraints = [
        ('hr_plan_name_unique', 'unique(name)',
         'A plan with this name already exists. Please use a unique plan name.'),
    ]

    @api.constrains('name')
    def _check_unique_plan_name(self):
        for rec in self:
            if not rec.name:
                continue
            duplicate = self.search([
                ('name', '=ilike', rec.name.strip()),
                ('id', '!=', rec.id),
            ])
            if duplicate:
                raise ValidationError(
                    _('Plan name "%s" already exists. Please use a unique plan name.')
                    % rec.name
                )