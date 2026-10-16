from odoo import models, fields, _,api
from odoo.exceptions import UserError,ValidationError


class CrmLead(models.Model):
    _inherit = "crm.lead"


    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        domain="[('is_company', '=', True)]",
        tracking=True,
    )

    new_ohc = fields.Boolean(
        string="New OHC",
        copy=False,
    )

    ohc_id = fields.Many2one(
        "ohc.management",
        string="OHC",
        readonly=True,
        copy=False,
    )

    project_id = fields.Many2one(
        "project.project",
        string="Project",
        readonly=True,
        copy=False,
    )

    def action_onboard_ohc(self):

        self.ensure_one()

        if self.probability != 100:
            raise UserError(_("Only Won Opportunities can be onboarded."))

        if self.ohc_id:
            raise UserError(_("OHC already onboarded."))
        
        if not self.partner_id.customer_code:
                    raise UserError(
                        _("Please enter the Customer Code for customer '%s' before onboarding the OHC.")
                        % self.partner_id.name
                    )

        return {
            'name': _('Onboard OHC'),
            'type': 'ir.actions.act_window',
            'res_model': 'onboard.ohc.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'default_customer_id':  self.partner_id.id, 
                # 'default_company_id': self.company_id.id,
                # 'default_company_id': self.partner_id.id,
                'default_email': self.email_from,
                'default_mobile': self.phone,
            }
        }

    @api.constrains('name')
    def _check_duplicate_lead(self):
        for rec in self:
            if not rec.name:
                continue

            duplicate = self.search([
                ('name', '=ilike', rec.name.strip()),
                ('id', '!=', rec.id),
            ], limit=1)

            if duplicate:
                raise ValidationError(_(
                    "A Lead with the name '%s' already exists. "
                    "Lead Name must be unique."
                ) % rec.name)