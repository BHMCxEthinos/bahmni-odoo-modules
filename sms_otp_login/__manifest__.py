{
    'name': 'SMS OTP Two-Factor Authentication (Nettyfish)',
    'version': '16.0.1.0.0',
    'summary': 'Mandatory SMS-based OTP verification after password login',
    'category': 'Extra Tools',
    'author': 'Custom',
    'depends': ['web', 'base'],
    'data': [
        'views/res_users_views.xml',
        'views/sms_otp_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
