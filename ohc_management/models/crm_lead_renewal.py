import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CrmLeadRenewal(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def cron_create_renewal_leads(self):
        """Called by the Scheduled Action. For won opportunities whose
        renewal_date has passed, creates a renewal follow-up lead."""
        today = fields.Date.context_today(self)
        expiring = self.search([
            ('renewal_date', '!=', False),
            ('renewal_date', '<=', today),
            ('x_renewal_processed', '=', False),
            ('active', '=', True),
            ('type', '=', 'opportunity'),
            ('stage_id.is_won', '=', True),
        ])
        if not expiring:
            _logger.info("Renewal cron: no expiring leads found.")
            return

        renewal_stage = self.env['crm.stage'].search(
            [('name', '=', 'Renewal Follow-up')], limit=1
        )
        if not renewal_stage:
            _logger.warning("Renewal cron: 'Renewal Follow-up' stage not found, skipping.")
            return

        for lead in expiring:
            new_lead = lead.copy({
                'name': lead.name + ' (Renewal)',
                'x_category': 'Renewal',
                'x_parent_lead_id': lead.id,
                'stage_id': renewal_stage.id,
                'x_renewal_processed': False,
                'renewal_date': False,
            })
            new_lead.activity_schedule(
                'mail.mail_activity_data_todo',
                summary='Follow up on renewal',
                note='Auto-created renewal from %s' % lead.name,
                user_id=new_lead.user_id.id or self.env.uid,
            )
            lead.write({'x_renewal_processed': True})
            _logger.info("Renewal cron: lead %s -> renewal lead %s created", lead.id, new_lead.id)