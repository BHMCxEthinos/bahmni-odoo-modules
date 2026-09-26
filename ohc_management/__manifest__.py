# -*- coding: utf-8 -*-

{
    'name': 'OHC Management',
    'version': '16.0.1.0.0',
    'category': 'Operations',
    'summary': 'OHC Management Module',
    'description': 'Manage OHC Operations',
    'author': 'Pritee Rathod',
    'depends': ['base', 'mail', 'project', 'hr', 'maintenance', 'fleet', 'hr_fleet', 'sale', 'crm','servia_calibration_log'],
    'data': [
        
        'security/ohc_groups.xml',
        'security/ohc_rules.xml',
        'security/survey_security.xml',
        'security/ir.model.access.csv',
        'data/ohc_sequence.xml',
        'views/ohc_alert_crons.xml',
        'views/ohc_views.xml',
        'views/hr_employee_views.xml',
        'views/ohc_columns_all_views.xml',
        'views/sale_order_b2b_crm_views.xml',
        'views/fleet_view.xml',
        'views/stock_internal_transfer.xml',
        'views/res_partner_view.xml',
        # 'views/ohc_security_views.xml',

        'views/survey_menu.xml',
        'views/survey_wizard_views.xml',
        'views/helpdesk_ticket_views.xml',
        'views/maintenance_menu_inherit.xml',
        'views/maintenance_equipment_form_hide_cost.xml',
        'views/helpdesk_ticket_form_hide_fields.xml',
        'views/fleet_vehicle_form_hide_fields.xml',
        'views/crm_lead_views.xml',
        'views/shift.xml'
      
    ],
    'assets': {
    'web.assets_backend': [
        'ohc_management/static/src/css/stat_button.css',
        'ohc_management/static/src/js/ohc_ambulance_log_form.js',
        'ohc_management/static/src/js/import_records.js',
        'ohc_management/static/src/xml/import_records.xml',
        'ohc_management/static/src/js/delete_visibility.js',
        
    ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}