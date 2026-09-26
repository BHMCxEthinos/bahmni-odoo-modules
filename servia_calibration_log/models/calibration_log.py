from odoo import api, fields, models
from datetime import timedelta

# Key used to store the reminder window in ir.config_parameter.
# Never hardcode the "30" days anywhere else in the module - always read it
# from here via _get_reminder_days().
REMINDER_DAYS_PARAM = 'servia_calibration_log.reminder_days'
REMINDER_DAYS_DEFAULT = 30


class ServiaCalibrationLog(models.Model):
    _name = 'servia.calibration.log'
    _description = 'Equipment Calibration Log'
    _order = 'cal_date desc'
    _rec_name = 'equipment_id'

    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment', required=True)
    cal_date = fields.Date('Calibration Date', default=fields.Date.context_today)
    calibrated_by = fields.Char('Calibrated By')
    cert_no = fields.Char('Certificate No')
    result = fields.Selection([
        ('pass', 'Pass'), ('fail', 'Fail'), ('adjusted', 'Adjusted'),
    ], string='Result', default='pass')
    next_due = fields.Date('Next Due')
    note = fields.Text('Notes')
    document = fields.Binary('Certificate / Document')
    document_filename = fields.Char('Document Filename')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], default='draft')
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.user.company_id)

    # True once the reminder activity has been created for this record's
    # next_due date, so the cron never nags twice for the same due date.
    # A new calibration always creates a NEW record (reminder_sent=False),
    # so this resets naturally every cycle.
    reminder_sent = fields.Boolean(string='Reminder Sent', copy=False, default=False)

    def action_confirm(self):
        for rec in self:
            rec.write({'state': 'confirmed'})

    def action_reset(self):
        for rec in self:
            rec.write({'state': 'draft'})

    is_overdue = fields.Boolean(string='Overdue', compute='_compute_due_status')
    is_due_soon = fields.Boolean(string='Due Soon', compute='_compute_due_status')

    @api.model
    def _get_reminder_days(self):
        """Read the configurable reminder window (days before Next Due).
        Falls back to REMINDER_DAYS_DEFAULT if the admin never set it."""
        param = self.env['ir.config_parameter'].sudo().get_param(
            REMINDER_DAYS_PARAM, default=REMINDER_DAYS_DEFAULT)
        try:
            return int(param)
        except (TypeError, ValueError):
            return REMINDER_DAYS_DEFAULT

    @api.depends('next_due')
    def _compute_due_status(self):
        today = fields.Date.context_today(self)
        reminder_days = self._get_reminder_days()
        soon_limit = today + timedelta(days=reminder_days)
        for rec in self:
            rec.is_overdue = bool(rec.next_due and rec.next_due < today)
            rec.is_due_soon = bool(rec.next_due and today <= rec.next_due <= soon_limit)

    @api.model
    def _cron_send_calibration_reminders(self):
        """Daily cron: for every confirmed calibration whose Next Due falls
        inside the configurable reminder window -
          1) create an Activity on the equipment record (in-app visibility)
          2) send the editable 'Calibration Reminder' email template to:
             - the equipment's OHC Operation Manager, if set; else
             - the equipment's Technician / Owner; else
             - the configured fallback email (Settings > Calibration)
        then mark it sent so it isn't repeated for the same due date.
        """
        today = fields.Date.context_today(self)
        reminder_days = self._get_reminder_days()
        target_date = today + timedelta(days=reminder_days)

        due_logs = self.search([
            ('state', '=', 'confirmed'),
            ('reminder_sent', '=', False),
            ('next_due', '!=', False),
            ('next_due', '>=', today),
            ('next_due', '<=', target_date),
        ])

        template = self.env.ref(
            'servia_calibration_log.email_template_calibration_reminder',
            raise_if_not_found=False)
        fallback_email = self.env['ir.config_parameter'].sudo().get_param(
            'servia_calibration_log.reminder_fallback_email', default='')

        for log in due_logs:
            equipment = log.equipment_id
            if not equipment:
                continue

            # 1) Preferred recipient: the OHC's Operation Manager.
            #    equipment.ohc_id -> ohc.management, .operation_manager -> hr.employee
            #    Guarded with _fields checks so this module doesn't hard-crash
            #    if the OHC module isn't installed on some other database.
            recipient_email = False
            ohc_manager = False
            if 'ohc_id' in equipment._fields and equipment.ohc_id:
                ohc_record = equipment.ohc_id
                if 'operation_manager' in ohc_record._fields and ohc_record.operation_manager:
                    ohc_manager = ohc_record.operation_manager
                    recipient_email = ohc_manager.work_email or (
                        ohc_manager.user_id.email if ohc_manager.user_id else False)

            # 2) Fall back to the equipment's Technician / Owner.
            responsible = equipment.technician_user_id or equipment.owner_user_id
            if not recipient_email and responsible:
                recipient_email = responsible.email

            # 3) Final fall back: the configured fallback email from Settings.
            if not recipient_email:
                recipient_email = fallback_email

            # In-app activity: assign to the Technician/Owner if there is one,
            # else the OHC manager's user account, else the current user.
            activity_user = responsible or (
                ohc_manager.user_id if ohc_manager and ohc_manager.user_id else False) or self.env.user
            equipment.activity_schedule(
                act_type_xmlid='mail.mail_activity_data_todo',
                date_deadline=log.next_due,
                summary='Calibration due: %s' % (equipment.name or ''),
                note='Next calibration date for %s is %s. Certificate no: %s' % (
                    equipment.name or '', log.next_due, log.cert_no or 'N/A'),
                user_id=activity_user.id,
            )

            # Actual email, using the editable template. Skipped only if
            # there is truly no address to send to.
            if template and recipient_email:
                template.sudo().send_mail(
                    log.id,
                    force_send=True,
                    email_values={'email_to': recipient_email},
                )

            log.reminder_sent = True
