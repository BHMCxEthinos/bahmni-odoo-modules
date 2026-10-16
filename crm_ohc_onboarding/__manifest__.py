# -*- coding: utf-8 -*-

{
    'name': 'CRM OHC Onboarding',
    'version': '16.0.1.0.0',
    'summary': 'Create OHC from Won CRM Opportunity',
    'description': """
CRM OHC Onboarding
==================

This module extends CRM to provide an OHC onboarding process.

Features
--------
* Adds "Onboard OHC" button on Won Opportunities
* Creates OHC Management record
* Links CRM Lead with OHC
* Automatically checks New OHC flag
* Prevents duplicate onboarding

Future Enhancements
-------------------
* Create Project
* Create Warehouse
* Create Stock Location
* Create Picking Types
* Create Analytic Account

""",

    'author': 'Pritee Rathod',

    'category': 'CRM',
    'license': 'LGPL-3',

    'depends': [
        'crm',
        'mail',
        'sale',
        'bahmni_sale',
        'bahmni_api_feed',
        'project',
        'ohc_management',      
    ],

    'data': [
        'security/ir.model.access.csv',

        'views/crm_lead_view.xml',
        'views/onboard_ohc_wizard.xml'
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}