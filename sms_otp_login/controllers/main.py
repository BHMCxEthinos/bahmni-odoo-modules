import functools
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

SESSION_PENDING_KEY = 'sms_otp_pending_uid'


_Home = None
try:
    from odoo.addons.web.controllers.main import Home as _Home
except ImportError:
    try:
        from odoo.addons.web.controllers.home import Home as _Home
    except ImportError:
        _Home = None

if _Home is None:
    _logger.error(
        "SMS_OTP_DEBUG: Could not locate the Home login controller class. "
        "SMS OTP will NOT be enforced until this is fixed."
    )
else:
    _logger.warning(
        "SMS_OTP_DEBUG: Patching web_login on %s.%s",
        _Home.__module__, _Home.__name__,
    )
    _original_web_login = _Home.web_login

    @functools.wraps(_original_web_login)
    def _sms_otp_web_login(self, redirect=None, **kw):
        _logger.warning(
            "SMS_OTP_DEBUG: web_login ENTERED (patched), method=%s",
            request.httprequest.method,
        )
        response = _original_web_login(self, redirect=redirect, **kw)

        if request.httprequest.method == 'POST' and request.session.uid:
            user = request.env['res.users'].sudo().browse(request.session.uid)

            if user.otp_mobile_number:
                _logger.warning(
                    "SMS_OTP_DEBUG: password OK for uid=%s, mobile=%s -> "
                    "pausing session and sending OTP",
                    request.session.uid, user.otp_mobile_number,
                )
                request.session[SESSION_PENDING_KEY] = request.session.uid
                request.session.uid = None

                try:
                    user._generate_and_send_sms_otp()
                except Exception:
                    _logger.exception("SMS OTP: could not send OTP on login")
                    request.session.pop(SESSION_PENDING_KEY, None)
                    return request.render('web.login', {
                        'error': 'Could not send OTP SMS. Contact your administrator.',
                    })

                url = '/web/login/sms_otp'
                if redirect:
                    url += '?redirect=%s' % redirect
                return request.redirect(url)
            else:
                _logger.warning(
                    "SMS_OTP_DEBUG: uid=%s has NO otp_mobile_number set -> "
                    "skipping OTP, normal login proceeds",
                    request.session.uid,
                )

        return response

    if hasattr(_original_web_login, 'routing'):
        _sms_otp_web_login.routing = _original_web_login.routing

    _Home.web_login = _sms_otp_web_login


class SMSOTPVerify(http.Controller):

    @http.route('/web/login/sms_otp', type='http', auth='none', sitemap=False, csrf=True)
    def web_login_sms_otp(self, redirect=None, **kw):
        pending_uid = request.session.get(SESSION_PENDING_KEY)
        if not pending_uid:
            return request.redirect('/web/login')

        error = None
        user = request.env['res.users'].sudo().browse(pending_uid)

        if request.httprequest.method == 'POST':
            if kw.get('resend'):
                user._generate_and_send_sms_otp()
                error = 'A new OTP has been sent.'
            else:
                otp_input = kw.get('otp', '')
                if user._verify_sms_otp(otp_input):
                    user._clear_sms_otp()
                    request.session.pop(SESSION_PENDING_KEY, None)

                    request.session.uid = pending_uid
                    request.session.login = user.login
                    request.session.session_token = user._compute_session_token(
                        request.session.sid
                    )
                    request.update_env(user=pending_uid)

                    return request.redirect(redirect or '/web')
                else:
                    error = 'Invalid or expired OTP. Please try again.'

        return request.render('sms_otp_login.otp_form', {
            'error': error,
            'redirect': redirect,
        })
