# models/res_partner.py

from odoo import models, fields

# class ResPartner(models.Model):
#     _inherit = 'res.partner'

#     customer_code = fields.Char(string="Customer Code")


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_code = fields.Char(string="Customer Code")

    @api.constrains('customer_code')
    def _check_customer_code_length(self):
        for rec in self:
            if rec.customer_code and len(rec.customer_code) > 7:
                raise ValidationError(
                    _("Customer Code cannot be more than 7 characters.")
                )