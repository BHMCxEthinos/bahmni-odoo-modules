from odoo import models, fields,api

class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    survey_type = fields.Selection(
            selection=[
                ('common', 'Common'),
                ('private', 'Private'),
            ],
            string='Type',
        )

    current_ohc_id = fields.Many2one(
        'ohc.management',
        string='Current OHC'
    )
    
    user_ids = fields.Many2many(
        'res.users',
        'survey_survey_res_users_rel',
        'survey_id',
        'user_id',
        string='Responsible',
        domain=[('share', '=', False)],
    )
   
    ohc_ids = fields.Many2many(
        'ohc.management',
        string='OHC'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        survey_type = self.env.context.get('survey_type')
        if survey_type:
            res['survey_type'] = survey_type

        return res


   


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    ohc_id = fields.Many2one(
        'ohc.management',
        string='OHC'
    )

    @api.model
    def create(self, vals):

        survey_id = vals.get('survey_id')

        if survey_id:

            survey = self.env['survey.survey'].browse(
                survey_id
            )

            if survey.current_ohc_id:
                vals['ohc_id'] = survey.current_ohc_id.id

        return super().create(vals)