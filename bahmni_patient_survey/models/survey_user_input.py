from odoo import fields, models


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    bahmni_patient_identifier = fields.Char('Patient ID', index=True, readonly=True)
    bahmni_patient_uuid = fields.Char('Patient UUID', readonly=True)
    bahmni_visit_uuid = fields.Char('Visit UUID', index=True, readonly=True)
    bahmni_reference = fields.Char(
        'Bahmni Reference', index=True, readonly=True, copy=False,
        help="Unique key from Bahmni, e.g. CSAT:<visit uuid> or NPS:2026-H2:<patient uuid>. "
             "A retry with the same key re-uses the unanswered participation instead of creating a new one.")
