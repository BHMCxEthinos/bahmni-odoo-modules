# -*- coding: utf-8 -*-

{
    'name': 'OHC Management',
    'version': '16.0.1.0.0',
    'category': 'Operations',
    'summary': 'OHC Management Module',
    'description': 'Manage OHC Operations',
    'author': 'Pritee Rathod',
    'depends': ['base', 'mail','project','hr','maintenance','fleet'],
    'data': [
        
        'security/ohc_groups.xml',
        'security/ohc_rules.xml',
        'security/ir.model.access.csv',
        'data/ohc_sequence.xml',
        'views/ohc_views.xml',
        'views/hr_employee_views.xml',
        'views/fleet_view.xml',
        'views/stock_internal_transfer.xml',
        'views/res_partner_view.xml',
        # 'views/ohc_security_views.xml',

        'views/survey_menu.xml',
        'views/survey_wizard_views.xml',
        'views/helpdesk_ticket_views.xml'
      
    ],
    'assets': {
    'web.assets_backend': [
        'ohc_management/static/src/css/stat_button.css',
    ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}