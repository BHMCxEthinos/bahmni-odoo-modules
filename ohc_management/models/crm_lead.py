# models/crm_lead.py

from odoo import models, _,fields,api
from odoo.exceptions import UserError
from datetime import date ,timedelta

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    renewal_date = fields.Date(string="Renewal Date")
    contract_start_date=fields.Date(string="Contract Start Date")
    contract_end_date=fields.Date(string="Contract End Date")

    @api.onchange('contract_end_date')
    def _onchange_contract_end_date(self):
        if self.contract_end_date:
            self.renewal_date = self.contract_end_date - timedelta(days=90)

    @api.constrains('renewal_date')
    def _check_renewal_date(self):
        for rec in self:
            if rec.renewal_date and rec.renewal_date < date.today():
                raise UserError(
                    _("Renewal Date cannot be a past date.")
                )

    def action_set_won_rainbowman(self):
        for lead in self:
            if not lead.partner_id:
                raise UserError(
                    _("Please select a customer before marking the opportunity as Won.")
                )

            if not lead.partner_id.customer_code:
                raise UserError(
                    _("Please enter the Customer Code for customer '%s' before marking this opportunity as Won.")
                    % lead.partner_id.name
                )
            if not lead.renewal_date:
                raise UserError(
                    _("Please enter the Renewal Date before marking the opportunity as Won.")
                )


        return super().action_set_won_rainbowman()