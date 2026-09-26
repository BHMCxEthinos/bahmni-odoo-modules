# -*- coding: utf-8 -*-

{
    'name': 'OHC OpenMRS Employee Synchronization',
    'version': '16.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Automatically create OpenMRS users when employees are assigned to an OHC.',
    'description': """
OHC OpenMRS Employee Synchronization

Features
========
* Automatically sync employees to OpenMRS
* Create OpenMRS users
* Check existing users
* Store OpenMRS UUID
* Generate random passwords
* Retry failed sync
* Company-wise configuration
* Logging
""",
    'author': 'Pritee Rathod',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'mail',
        'hr',
        'ohc_management',
    ],

    'data': [
        # 'security/ir.model.access.csv'
        # 'data/openmrs_user_email_template.xml',
        'views/res_users_views.xml',
        
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}