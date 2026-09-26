# models/crm_lead.py

from odoo import models, _,fields,api
from odoo.exceptions import UserError
from datetime import date ,timedelta
from odoo.exceptions import ValidationError

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    renewal_date = fields.Date(string="Renewal Date")
    contract_start_date=fields.Date(string="Contract Start Date")
    contract_end_date=fields.Date(string="Contract End Date")
    email_from = fields.Char(
            string='Email',
            required=True,
        )
    phone = fields.Char(
            string='Phone',
            required=True,
        )

    @api.onchange('contract_end_date')
    def _onchange_contract_end_date(self):
        if self.contract_end_date:
            self.renewal_date = self.contract_end_date - timedelta(days=90)

    
    @api.constrains('contract_start_date', 'renewal_date')
    def _check_renewal_date(self):
        for rec in self:

            # 1. Contract Start Date cannot be in the past
            # if rec.contract_start_date and rec.contract_start_date < date.today():
            #     raise ValidationError(
            #         _("Contract Start Date cannot be a past date.")
            #     )

            # 2. Contract End / Renewal Date cannot be in the past
            if rec.renewal_date and rec.renewal_date < date.today():
                raise ValidationError(
                    _("Contract End Date cannot be a past date.")
                )

            # 3. Contract End Date cannot be before Contract Start Date
            if (
                rec.contract_start_date
                and rec.renewal_date
                and rec.renewal_date < rec.contract_start_date
            ):
                raise ValidationError(
                    _("Contract End Date cannot be earlier than the Contract Start Date.")
                )
    def _get_missing_won_fields(self):
        """Returns a list of missing field labels required to mark this lead as Won."""
        self.ensure_one()
        missing = []
        if not self.contract_start_date:
            missing.append(_("Contract Start Date"))
        if not self.contract_end_date:
            missing.append(_("Contract End Date"))
        if not self.renewal_date:
            missing.append(_("Renewal Date"))
        return missing

    @api.constrains('renewal_date', 'contract_start_date', 'contract_end_date', 'stage_id')
    def _check_required_fields_on_won(self):
        for rec in self:
            if rec.stage_id and rec.stage_id.is_won:
                missing = rec._get_missing_won_fields()
                if missing:
                    raise ValidationError(
                        _("Cannot mark this opportunity as Won. Please fill in: %s")
                        % ", ".join(missing)
                    )

    def action_set_won_rainbowman(self):
        for lead in self:
            if not lead.partner_id:
                raise UserError(
                    _("Please select a customer before marking the opportunity as Won.")
                )

            missing = lead._get_missing_won_fields()
            if missing:
                raise UserError(
                    _("Cannot mark this opportunity as Won. Please fill in: %s")
                    % ", ".join(missing)
                )

        return super().action_set_won_rainbowman()


    def action_sale_quotations_new(self):
        action = super().action_sale_quotations_new()
        action.setdefault('context', {})

        shop_field = self.env['sale.order']._fields.get('shop_id')
        presales_shop_id = False
        if shop_field:
            presales_shop = self.env[shop_field.comodel_name].search(
                [('name', '=', 'Pre-Sales')], limit=1
            )
            presales_shop_id = presales_shop.id if presales_shop else False

        b2b_categ = self.env['product.category'].search(
            [('complete_name', '=', 'All / Services')], limit=1
        )

        raise UserError(_(
            "DEBUG -> shop_field found: %s | presales_shop_id: %s | b2b_categ_id: %s"
        ) % (bool(shop_field), presales_shop_id, b2b_categ.id if b2b_categ else False))

        action['context'].update({
            'is_b2b_crm': True,
            'crm_b2b_categ_id': b2b_categ.id if b2b_categ else False,
        })
        if presales_shop_id:
            action['context']['default_shop_id'] = presales_shop_id

        return action