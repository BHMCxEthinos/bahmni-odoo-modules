from odoo import models, fields, api


class SurveySelectionWizard(models.TransientModel):
    _name = 'survey.selection.wizard'
    _description = 'Survey Selection Wizard'

    ohc_id = fields.Many2one(
        'ohc.management',
        string='OHC',
        readonly=True,
        required=True,
    )

    # survey_id = fields.Many2one(
    #     'survey.survey',
    #     string='Checklist Form',
    #     required=True,
    # )
    # survey_id = fields.Many2one(
    #     'survey.survey',
    #     string='Checklist Form',
    #     required=True,
    #     domain="['|', ('survey_type', '!=', 'private'), ('user_id', '=', uid)]"
    # )
    survey_id = fields.Many2one(
    'survey.survey',
    string='Checklist Form',
    required=True,
    domain="['|', ('survey_type', '!=', 'private'), ('user_ids', 'in', [uid])]"
)

    @api.onchange('ohc_id')
    def _onchange_ohc(self):
        return {
            'domain': {
                'survey_id': [
                    ('ohc_ids', 'in', self.ohc_id.id)
                ]
            }
        }

   
   

    def action_open_survey(self):

        self.ensure_one()

        answer = self.survey_id._create_answer(
            user=self.env.user,
            partner=self.env.user.partner_id,
            ohc_id=self.ohc_id.id,
        )
        if answer.ohc_id.id != self.ohc_id.id:
            answer.sudo().write({'ohc_id': self.ohc_id.id})

        return {
            'type': 'ir.actions.act_url',
            'url': '/survey/%s/%s' % (
                self.survey_id.access_token,
                answer.access_token,
            ),
            'target': 'new',
        }

