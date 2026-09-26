from odoo import models, fields, api
from datetime import date, timedelta

class ComplianceRecord(models.Model):
    _name = 'clinic.compliance.record'
    _description = 'Compliance Record'
    _rec_name = 'record_name'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    record_name = fields.Char(
        string='Name',
        compute='_compute_record_name',
        store=True)

    # ondelete='set null'   OHC delete ???????? auto NULL ????
    clinic_id = fields.Many2one(
        'ohc.management',
        string='OHC',
        required=True,
        ondelete='restrict')

    # ondelete='set null'   Compliance Master delete ???????? auto NULL ????
    master_id = fields.Many2one(
        'clinic.compliance.master',
        string='Compliance',
        required=True,
        ondelete='restrict')

    status = fields.Selection([
        ('green', 'Valid'),
        ('orange', 'Expiring Soon'),
        ('red', 'Expired')
    ], string='Status')

    expiry_date = fields.Date(string='Expiry Date')

    actual_renewal_date = fields.Date(
        string="Actual Renewal Date",
    )

    document_ids = fields.Many2many(
        'ir.attachment',
        'compliance_record_attachment_rel',
        'record_id',
        'attachment_id',
        string='Documents')

    edit_unlocked = fields.Boolean(
    string='Edit Unlocked',
    compute='_compute_edit_unlocked')

    pending_edit_reason = fields.Text(string='Pending Edit Reason')

    last_edit_reason = fields.Text(string='Last Edit Reason', readonly=True)

    @api.depends('clinic_id', 'master_id')
    def _compute_record_name(self):
        for rec in self:
            # Try-except   record deleted ???? ??? crash ????
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

    @api.depends()
    def _compute_edit_unlocked(self):
        ctx_unlocked = self.env.context.get('edit_unlocked', False)
        for rec in self:
            rec.edit_unlocked = True if not rec.id else ctx_unlocked

    def _refresh_status(self):
        """Recompute status for a single record (shared by cron + manual refresh)."""
        self.ensure_one()
        if not self.expiry_date:
            if self.status:
                self.status = False
            return
        today = date.today()
        try:
            warning_days = self.master_id.period_days if self.master_id and self.master_id.period_days else 30
            old_status = self.status
            if self.expiry_date <= today:
                self.status = 'red'
            elif self.expiry_date <= today + timedelta(days=warning_days):
                self.status = 'orange'
            else:
                self.status = 'green'
            if self.status != old_status and self.status in ['orange', 'red']:
                self._send_compliance_notification()
        except Exception:
            pass

    def action_update_status(self):
        """Cron job: bulk update status for all records with an expiry date."""
        records = self.sudo().search([('expiry_date', '!=', False)])
        for rec in records:
            rec._refresh_status()

    def action_refresh_record(self):
        """Refresh button: recompute this record's status now, no cron wait."""
        self.ensure_one()
        self._refresh_status()
        return True

    def action_request_edit(self):
        """List-view Edit button: opens confirmation popup before unlocking fields."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirm Edit',
            'res_model': 'clinic.compliance.edit.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_record_id': self.id},
        }


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
                self.with_context(mail_notify_force_send=False).message_post(
                    body=body,
                    subject=subject,
                    message_type='email',
                    partner_ids=partner_ids,
                    subtype_xmlid='mail.mt_comment',
                )
        except Exception as e:
            # Notification fail ???? ??? crash ????
            pass


    @api.model
    def create(self, vals):
        record = super().create(vals)
        if vals.get('document_ids'):
            for doc in record.document_ids:
                record.message_post(
                    body=f'Document uploaded: <b>{doc.name}</b> by {record.env.user.name}',
                    message_type='comment',
                    subtype_xmlid='mail.mt_note',
                )
        return record

    def write(self, vals):
        old_docs = set(self.document_ids.ids)
        result = super().write(vals)

        if 'expiry_date' in vals:
            for rec in self:
                rec._refresh_status()

        if 'document_ids' in vals:
            new_docs = set(self.document_ids.ids)
            added_ids = new_docs - old_docs
            removed_ids = old_docs - new_docs
            if added_ids:
                added_docs = self.env['ir.attachment'].browse(added_ids)
                for doc in added_docs:
                    self.message_post(
                        body=f'Document uploaded: <b>{doc.name}</b> by {self.env.user.name}',
                        message_type='comment',
                        subtype_xmlid='mail.mt_note',
                    )
            if removed_ids:
                removed_docs = self.env['ir.attachment'].sudo().browse(removed_ids)
                for doc in removed_docs:
                    self.message_post(
                        body=f'Document removed: <b>{doc.name}</b> by {self.env.user.name}',
                        message_type='comment',
                        subtype_xmlid='mail.mt_note',
                    )

        return result      