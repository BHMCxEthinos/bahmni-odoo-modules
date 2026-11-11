{
    'name': 'Bahmni Patient Survey',
    'version': '16.0.1.0.0',
    'summary': 'Personal NPS/CSAT survey links for Bahmni patients, sent by the Bahmni scheduler',
    'description': """
Lets the Bahmni (OpenMRS) feedback scheduler ask Odoo for a personal survey link
for one patient, so the patient's answers are stored against their own contact
(res.partner) and, for CSAT, against the visit they are rating.
    """,
    'author': 'IPLit',
    'category': 'Marketing/Surveys',
    'license': 'LGPL-3',
    'depends': ['survey'],
    'data': [
        'views/survey_user_input_views.xml',
    ],
    'installable': True,
    'application': False,
}
