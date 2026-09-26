from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    calibration_reminder_days = fields.Integer(
        string='Calibration Reminder (days before due)',
        config_parameter='servia_calibration_log.reminder_days',
        default=30,
        help="How many days before an equipment's Next Due date the "
             "reminder activity and email should be created for the "
             "technician.",
    )
    calibration_reminder_fallback_email = fields.Char(
        string='Fallback Reminder Email',
        config_parameter='servia_calibration_log.reminder_fallback_email',
        help="Reminder emails go to the equipment's OHC Operation Manager "
             "first, then its Technician/Owner. This address is used only "
             "if none of those are set. Leave blank to skip sending in "
             "that case.",
    )
