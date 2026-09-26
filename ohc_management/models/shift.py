from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ShiftType(models.Model):
    _inherit = 'shift.type'
    _description = 'Shift Type'

    # name = fields.Char(
    #     string="Name",
    #     required=True
    # )

    _sql_constraints = [
        (
            'shift_type_name_unique',
            'UNIQUE(name)',
            'Shift name must be unique.'
        ),
    ]

    @api.constrains('name')
    def _check_duplicate_shift_name(self):
        for record in self:
            if not record.name:
                continue

            duplicate = self.search([
                ('id', '!=', record.id),
                ('name', '=ilike', record.name.strip()),
            ], limit=1)

            if duplicate:
                raise ValidationError(
                    "Shift name '%s' already exists. "
                    "Duplicate shift names are not allowed."
                    % record.name
                )



class EmployeeShift(models.Model):
    _inherit = 'hr.shift' 

    @api.constrains('time_from', 'time_too')
    def _check_shift_time(self):
        for record in self:
            if record.time_from and record.time_too:
                if record.time_too <= record.time_from:
                    raise ValidationError(
                        "Time Too cannot be less than or equal to Time From."
                    )


class WeekWeek(models.Model):
    _inherit = 'week.week'
    _description = 'Employee Weekoffs'

    @api.constrains('name', 'code')
    def _check_unique_name_and_code(self):
        for record in self:
            # Check for duplicate Name
            if record.name:
                duplicate_name = self.search([
                    ('id', '!=', record.id),
                    ('name', '=ilike', record.name.strip()),
                ], limit=1)
                if duplicate_name:
                    raise ValidationError(
                        f"The Name '{record.name}' already exists!"
                    )

            # Check for duplicate Code
            if record.code:
                duplicate_code = self.search([
                    ('id', '!=', record.id),
                    ('code', '=', record.code.strip()),
                ], limit=1)
                if duplicate_code:
                    raise ValidationError(
                        f"The Day No '{record.code}' already exists!"
                    )

class WeekWeek(models.Model):
    _inherit = 'week.selection'
    _description = 'Employee Weekoffs'

    @api.constrains('name', 'code')
    def _check_unique_name_and_code(self):
        for record in self:
            # Check for duplicate Name
            if record.name:
                duplicate_name = self.search([
                    ('id', '!=', record.id),
                    ('name', '=ilike', record.name.strip()),
                ], limit=1)
                if duplicate_name:
                    raise ValidationError(
                        f"The Name '{record.name}' already exists!"
                    )

            # Check for duplicate Code
            if record.code:
                duplicate_code = self.search([
                    ('id', '!=', record.id),
                    ('code', '=', record.code.strip()),
                ], limit=1)
                if duplicate_code:
                    raise ValidationError(
                        f"The Day No '{record.code}' already exists!"
                    )

class AllocationWizard(models.TransientModel):
    _inherit = 'allocation.wizard'
    _description = 'Create Bulk Shift Allocations'


    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if (
                record.date_from
                and record.date_to
                and record.date_to <= record.date_from
            ):
                raise ValidationError(
                    "'Date To' cannot be less than or equla to 'Date From'."
                )