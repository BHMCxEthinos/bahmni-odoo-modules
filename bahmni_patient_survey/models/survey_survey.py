import logging

from odoo import _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    def bahmni_create_patient_answer(self, patient_uuid, patient_identifier=False, patient_name=False,
                                     phone=False, visit_uuid=False, reference=False):
        """Called by the Bahmni feedback scheduler over JSON-RPC.

        Finds (or creates) the patient's contact, creates a participation for this survey
        and returns the personal link to send by SMS:
            {'url': 'https://<odoo>/fb?t=<answer token>',
             'answer_id': <id>, 'partner_id': <id>, 'reused': bool}
        """
        self.ensure_one()
        # The caller must at least be allowed to read surveys (Survey user / officer).
        self.check_access_rights('read')
        self.check_access_rule('read')

        survey = self.sudo()
        if not survey.active:
            raise UserError(_("Survey '%s' is archived.") % survey.title)
        if survey.session_state in ('ready', 'in_progress'):
            raise UserError(_("Survey '%s' has a live session running. End the live session "
                              "so patients can open their link.") % survey.title)
        if survey.users_login_required:
            raise UserError(_("Survey '%s' requires login. Turn off 'Login Required' "
                              "so patients can answer from the SMS link.") % survey.title)

        partner = self._bahmni_find_or_create_partner(patient_uuid, patient_identifier, patient_name, phone)
        UserInput = self.env['survey.user_input'].sudo()

        answer = UserInput.browse()
        if reference:
            # Same visit / same NPS period retried (e.g. SMS failed last night): re-use it.
            answer = UserInput.search([
                ('survey_id', '=', survey.id),
                ('bahmni_reference', '=', reference),
                ('state', '!=', 'done'),
            ], limit=1)
        reused = bool(answer)
        if not answer:
            answer = survey._create_answer(
                partner=partner,
                check_attempts=False,
                bahmni_patient_identifier=patient_identifier or False,
                bahmni_patient_uuid=patient_uuid or False,
                bahmni_visit_uuid=visit_uuid or False,
                bahmni_reference=reference or False,
            )

        base_url = survey.get_base_url().rstrip('/')
        # Short form for SMS / DLT whitelisting (see controllers/main.py): <base>/fb?t=<answer token>
        url = '%s/fb?t=%s' % (base_url, answer.access_token)
        _logger.info("Bahmni survey link for patient %s on survey %s (answer %s, reused=%s)",
                     patient_identifier or patient_uuid, survey.id, answer.id, reused)
        return {'url': url, 'answer_id': answer.id, 'partner_id': partner.id, 'reused': reused}

    @api.model
    def _bahmni_find_or_create_partner(self, patient_uuid, patient_identifier, patient_name, phone):
        """Patients are synced from Bahmni as res.partner with ref = patient ID and
        uuid = patient UUID (bahmni_sale). Match on those; if the patient has not been
        synced yet, create the contact the same way so the sync later updates it."""
        Partner = self.env['res.partner'].sudo().with_context(active_test=False)
        has_uuid = 'uuid' in Partner._fields
        partner = Partner.browse()
        if patient_uuid and has_uuid:
            partner = Partner.search([('uuid', '=', patient_uuid)], limit=1)
        if not partner and patient_identifier:
            partner = Partner.search([('ref', '=', patient_identifier)], limit=1)
        if partner:
            return partner
        if not patient_identifier and not patient_uuid:
            raise UserError(_("Patient ID or UUID is required."))
        vals = {
            'name': patient_name or patient_identifier or patient_uuid,
            'ref': patient_identifier or False,
            'phone': phone or False,
            'customer_rank': 1,
        }
        if has_uuid:
            vals['uuid'] = patient_uuid or False
        return Partner.create(vals)
