# -*- coding: utf-8 -*-
{
    'name': 'Servia Equipment Calibration Log',
    'version': '16.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Log instrument and equipment calibration: equipment, calibrated-by, date, result and next-due date. Stay audit-ready for ISO / QA.',
    'description': """
Servia Equipment Calibration Log
================================
Track equipment calibration and due dates.

* Record each calibration: equipment, date and calibrated-by.
* Capture result and next-due date.
* Confirm records; filter and group by equipment or result.
* Simple calibration log for QA / ISO compliance.
* Works on Odoo Community, Enterprise and Odoo.sh, versions 12 to 19

Installation and customization by Servia - see the description page.
""",
    'author': 'Servia',
    'website': 'https://servia.ae',
    'license': 'LGPL-3',
    'price': 0.0,
    'currency': 'USD',
    'support': 'support@servia.ae',
    'depends': ['base', 'maintenance', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_config_parameter_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'views/servia_calibration_log_views.xml',
        'views/maintenance_equipment_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
