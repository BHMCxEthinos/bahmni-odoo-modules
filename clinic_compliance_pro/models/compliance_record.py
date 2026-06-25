from odoo import models, fields, api
from datetime import date, timedelta

class ComplianceRecord(models.Model):
    _name = 'clinic.compliance.record'
    _description = 'Compliance Record'
    _rec_name = 'record_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    record_name = fields.Char(
        string='Name',
        compute='_compute_record_name',
        store=True)

    # ondelete='set null' — OHC delete ???????? auto NULL ????
    clinic_id = fields.Many2one(
        'ohc.management',
        string='OHC',
        ondelete='set null')

    # ondelete='set null' — Compliance Master delete ???????? auto NULL ????
    master_id = fields.Many2one(
        'clinic.compliance.master',
        string='Compliance',
        ondelete='set null')

    status = fields.Selection([
        ('green', 'Valid'),
        ('orange', 'Expiring Soon'),
        ('red', 'Expired')
    ], string='Status', default='green')

    expiry_date = fields.Date(string='Expiry Date')

    document_ids = fields.Many2many(
        'ir.attachment',
        'compliance_record_attachment_rel',
        'record_id',
        'attachment_id',
        string='Documents')

    @api.depends('clinic_id', 'master_id')
    def _compute_record_name(self):
        for rec in self:
            # Try-except — record deleted ???? ??? crash ????
            try:
                clinic = rec.with_context(
                    active_test=False).clinic_id.name \
                    if rec.clinic_id else ''
            except Exception:
                clinic = ''
            try:
                master = rec.with_context(
                    active_test=False).master_id.name \
                    if rec.master_id else ''
            except Exception:
                master = ''

            if clinic and master:
                rec.record_name = f'{clinic} - {master}'
            elif clinic:
                rec.record_name = clinic
            elif master:
                rec.record_name = master
            else:
                rec.record_name = 'New Record'

    def action_update_status(self):
        today = date.today()
        warning_days = 30
        # sudo() — permission issues ???? ?????
        records = self.sudo().search([('expiry_date', '!=', False)])
        for rec in records:
            try:
                old_status = rec.status
                if rec.expiry_date <= today:
                    rec.status = 'red'
                elif rec.expiry_date <= today + timedelta(days=warning_days):
                    rec.status = 'orange'
                else:
                    rec.status = 'green'
                if rec.status != old_status and rec.status in ['orange', 'red']:
                    rec._send_compliance_notification()
            except Exception as e:
                # ?? record fail ???? ??? ???? ???? ??????
                continue

    def _send_compliance_notification(self):
        self.ensure_one()
        try:
            ohc_name = self.clinic_id.name if self.clinic_id else 'N/A'
            compliance_name = self.master_id.name if self.master_id else 'N/A'
            expiry = str(self.expiry_date) if self.expiry_date else 'N/A'

            if self.status == 'red':
                subject = f'?? Compliance Expired: {self.record_name}'
                body = f"""
                    <p>Dear Team,</p>
                    <p>The following compliance has <b>EXPIRED</b>:</p>
                    <ul>
                        <li><b>OHC:</b> {ohc_name}</li>
                        <li><b>Compliance:</b> {compliance_name}</li>
                        <li><b>Expiry Date:</b> {expiry}</li>
                        <li><b>Status:</b> ?? Expired</li>
                    </ul>
                    <p>Please renew immediately!</p>
                """
            else:
                subject = f'?? Compliance Expiring Soon: {self.record_name}'
                body = f"""
                    <p>Dear Team,</p>
                    <p>The following compliance is <b>EXPIRING SOON</b>:</p>
                    <ul>
                        <li><b>OHC:</b> {ohc_name}</li>
                        <li><b>Compliance:</b> {compliance_name}</li>
                        <li><b>Expiry Date:</b> {expiry}</li>
                        <li><b>Status:</b> ?? Expiring Soon</li>
                    </ul>
                    <p>Please renew within 30 days!</p>
                """

            partner_ids = []

            # Operations Manager
            if self.clinic_id and self.clinic_id.operation_manager:
                manager = self.clinic_id.operation_manager
                if hasattr(manager, 'user_id') and manager.user_id:
                    partner_ids.append(manager.user_id.partner_id.id)

            # ???? Internal Users
            internal_users = self.env['res.users'].sudo().search([
                ('share', '=', False),
                ('active', '=', True)
            ])
            for user in internal_users:
                partner_ids.append(user.partner_id.id)

            partner_ids.append(self.env.user.partner_id.id)
            partner_ids = list(set(filter(None, partner_ids)))

            if partner_ids:
                self.message_post(
                    body=body,
                    subject=subject,
                    message_type='email',
                    partner_ids=partner_ids,
                    subtype_xmlid='mail.mt_comment',
                )
        except Exception as e:
            # Notification fail ???? ??? crash ????
            pass