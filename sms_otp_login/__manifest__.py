{
    'name': 'SMS OTP Two-Factor Authentication',
    'version': '16.0.1.0.0',
    'summary': 'Mandatory SMS OTP 2FA for Odoo login (Nettyfish SMS provider)',
    'description': """
SMS OTP Two-Factor Authentication
==================================
After a user enters the correct password, this module sends a one-time
6-digit code via SMS (Nettyfish) to the mobile number configured on their
user profile, and does NOT let them in until they type that code.

Configuration is done ONLY via environment variables in docker-compose.yml
(NETTY_API_URL, NETTY_USER, NETTY_PASSWORD, NETTY_SENDERID, NETTY_ROUTE,
NETTY_CHANNEL, OTP_DEBUG_LOG) - no Odoo System Parameters are used.
""",
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
