from odoo import models, fields

class ResUsers(models.Model):
    _inherit = "res.users"

    clinical_user = fields.Boolean(
        string="Clinical User",
        default=False,
        help="Checked if this user exists in OpenMRS."
    )

    openmrs_user_uuid = fields.Char(
        string="OpenMRS User UUID",
        readonly=True,
        copy=False,
    )