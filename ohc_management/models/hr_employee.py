from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
<<<<<<< HEAD
from calendar import monthrange
from datetime import timedelta
WINDOW_DAYS = 31 
=======

>>>>>>> 8eaa44d131a3b00836da08466aa633a14b720292

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

<<<<<<< HEAD
    def _first_uncovered_date(self, start, end):
            """Return the first date between start and end with no shift
            allocation, or False if every day is covered."""
            self.ensure_one()
            ranges = sorted(
                (l.date_from, l.date_to)
                for l in self.shift_allocation_ids
                if l.date_from and l.date_to
                and l.date_to >= start and l.date_from <= end
            )
            cursor = start
            for d_from, d_to in ranges:
                if d_from > cursor:
                    return cursor              # gap found
                if d_to >= cursor:
                    cursor = d_to + timedelta(days=1)
                if cursor > end:
                    return False               # fully covered
            return cursor if cursor <= end else False

    
    @api.model
    def _cron_shift_allocation_check(self):
        today = fields.Date.context_today(self)
        end = today + timedelta(days=WINDOW_DAYS)

        pending = []
        for emp in self.search([('active', '=', True)]):
            missing = emp._first_uncovered_date(today, end)
            if missing:
                dates = emp.shift_allocation_ids.mapped('date_to')
                last = max(dates) if dates else False
                pending.append((emp, last, missing))

        if not pending:
            return

        # Recipients: HR managers + Operation Head
        # users = (self.env.ref('hr.group_hr_manager').users
        #          | self.env.ref('ohc_management.group_operation_head').users)
        # emails = [e for e in users.mapped('partner_id.email') if e]
        users = (self.env.ref('ohc_management.group_shift_alert_hr').users
         | self.env.ref('ohc_management.group_operation_head').users)
        users = users.filtered(lambda u: u.active and u.id != self.env.ref('base.user_admin').id)
        emails = [e for e in users.mapped('partner_id.email') if e]
        if not emails:
            return

        td = 'style="padding:4px 10px;border:1px solid #ccc"'
        rows = ''.join(
            '<tr><td %s>%s</td><td %s>%s</td><td %s>%s</td><td %s>%s</td></tr>' % (
                td, emp.name,
                td, emp.department_id.name or '-',
                td, last.strftime('%d/%m/%Y') if last else 'No allocation',
                td, missing.strftime('%d/%m/%Y'),
            )
            for emp, last, missing in pending
        )
        body = (
            '<p>Hello,</p>'
            '<p>The following employees do not have shifts allocated for the '
            'period <b>%s</b> to <b>%s</b>:</p>'
            '<table style="border-collapse:collapse">'
            '<tr><th %s>Employee</th><th %s>Department</th>'
            '<th %s>Allocated Till</th><th %s>First Missing Date</th></tr>'
            '%s</table>'
            '<p>Please allocate the shifts at the earliest.</p>'
        ) % (today.strftime('%d/%m/%Y'), end.strftime('%d/%m/%Y'),
             td, td, td, td, rows)

        self.env['mail.mail'].sudo().create({
            'subject': _('Shift allocation pending: %s to %s') % (
                today.strftime('%d/%m/%Y'), end.strftime('%d/%m/%Y')),
            'body_html': body,
            'email_to': ','.join(emails),
            'email_from': self.env.company.email or self.env.user.email_formatted,
        }).send()


=======
>>>>>>> 8eaa44d131a3b00836da08466aa633a14b720292
class HrPlan(models.Model):
    _inherit = 'hr.plan'

    @api.constrains('name')
    def _check_unique_plan_name(self):
        for rec in self:
            duplicate = self.search([
                ('name', '=', rec.name),
                ('id', '!=', rec.id),
            ])
            if duplicate:
                raise ValidationError(
                    _('Plan name "%s" already exists. Please use a unique plan name.')
                    % rec.name
                )