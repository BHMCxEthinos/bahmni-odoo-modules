# models/res_partner.py

from odoo import models, fields

# class ResPartner(models.Model):
#     _inherit = 'res.partner'

#     customer_code = fields.Char(string="Customer Code")


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re

class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_code = fields.Char(string="Customer Code")

    @api.constrains('customer_code')
    def _check_customer_code(self):
        for rec in self:
            if not rec.customer_code:
                continue

            customer_code = rec.customer_code.strip()

            # Exactly 7 characters
            if len(customer_code) != 7:
                raise ValidationError(
                    _("Customer Code must be exactly 7 characters.")
                )

            # Only letters and numbers
            if not re.match(r'^[A-Za-z0-9]+$', customer_code):
                raise ValidationError(
                    _("Customer Code can contain only letters and numbers. "
                    "Special characters and spaces are not allowed.")
                )

            # Unique customer code (case-insensitive)
            duplicate = self.search([
                ('customer_code', '=ilike', customer_code),
                ('id', '!=', rec.id),
            ], limit=1)

            if duplicate:
                raise ValidationError(
                    _("Customer Code '%s' already exists. "
                    "Please enter a unique Customer Code.")
                    % customer_code
                )


class ResUsers(models.Model):
    _inherit = 'res.users'

    def get_user_ohc_ids(self):
        self.ensure_one()

        self.env.cr.execute("""
            SELECT ohc_management_id
            FROM hr_employee_ohc_management_rel rel
            JOIN hr_employee e
                ON e.id = rel.hr_employee_id
            WHERE e.user_id = %s
        """, (self.id,))

        return [row[0] for row in self.env.cr.fetchall()]


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id_partner_domain(self):
        domain = []

        if self.picking_type_id and self.picking_type_id.name == 'Returns':
            domain = [('is_company', '=', False)]

        return {
            'domain': {
                'partner_id': domain
            }
        }