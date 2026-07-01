{
    'name': 'OHC Compliance',
    'version': '16.0.3.0',
    'depends': ['base', 'mail', 'account', 'ohc_management'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/compliance_views.xml',
        'views/template_views.xml',
        'views/dashboard_views.xml',
        'views/res_partner_views.xml',
        'views/wizard_views.xml',
        'views/ohc_management_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
}