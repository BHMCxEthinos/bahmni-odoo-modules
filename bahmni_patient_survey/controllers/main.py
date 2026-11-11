from odoo import http
from odoo.http import request

from odoo.addons.survey.controllers.main import Survey


class BahmniSurveyShortLink(Survey):
    """Short survey link for SMS: /fb?t=<answer token>.

    DLT (Airtel) only accepts dynamic URLs of the form <fixed part>?<params>,
    at most 120 characters, with no redirect. This route renders the same page
    as /survey/<survey token>/<answer token> directly, without redirecting.
    """

    @http.route('/fb', type='http', auth='public', website=True, sitemap=False)
    def bahmni_short_survey_link(self, t=None, **post):
        if not t:
            return request.not_found()
        answer = request.env['survey.user_input'].sudo().search([('access_token', '=', t)], limit=1)
        if not answer:
            return request.not_found()
        return self.survey_display_page(answer.survey_id.access_token, answer.access_token, **post)
