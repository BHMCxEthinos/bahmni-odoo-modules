<<<<<<< HEAD
# -*- coding: utf-8 -*-
import functools
import logging

import werkzeug.utils

=======
import functools
import logging

>>>>>>> 8eaa44d131a3b00836da08466aa633a14b720292
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

SESSION_PENDING_KEY = 'sms_otp_pending_uid'

<<<<<<< HEAD
# ---------------------------------------------------------------------
# We MONKEYPATCH Home.web_login instead of subclassing it.
#
# Why: Odoo's built-in `auth_totp` module ALSO subclasses the same Home
# controller and overrides web_login. When two addons both subclass the
# same controller for the same route, Odoo's routing picks whichever
# subclass "wins" the MRO - and in this stack that was auth_totp, so our
# subclass's extra code was silently never called (no errors, just never
# executed). Patching the method directly on the base Home class means
# every subclass (including auth_totp's) calls our patched version via
# super(), so our OTP step always runs after the password check succeeds.
# ---------------------------------------------------------------------
try:
    from odoo.addons.web.controllers.main import Home
except ImportError:
    from odoo.addons.web.controllers.home import Home

# IMPORTANT: use the original DECORATED function as-is - do NOT unwrap via
# `.__wrapped__`. Odoo's @http.route() decorator attaches a `.routing`
# attribute (and sometimes wraps the function for CORS/session handling)
# onto THIS object. Unwrapping past it loses `.routing`, which makes Odoo's
# routing map silently drop the URL entirely (no exception - the route
# just stops resolving, i.e. a 404 on /web/login).
_original_web_login = Home.web_login


@functools.wraps(_original_web_login)
def _patched_web_login(self, redirect=None, **kw):
    _logger.warning("SMS_OTP_DEBUG: web_login ENTERED (patched)")

    response = _original_web_login(self, redirect=redirect, **kw)

    if http.request.httprequest.method == 'POST' and request.session.uid:
        uid = request.session.uid
        _logger.warning("SMS_OTP_DEBUG: password OK for uid=%s", uid)

        user = request.env['res.users'].sudo().browse(uid)
        if user.otp_mobile_number:
            _logger.warning(
                "SMS_OTP_DEBUG: user %s has otp_mobile_number set, pausing session for OTP",
                user.login,
            )
            # Pause the session: remember who logged in with password,
            # but blank out uid so Odoo does NOT treat them as logged in yet.
            request.session[SESSION_PENDING_KEY] = uid
            request.session.uid = None

            user._generate_and_send_sms_otp()

            otp_redirect = werkzeug.utils.redirect('/web/login/sms_otp')
            # Odoo's built-in auth_signup module also wraps web_login and
            # unconditionally does `response.qcontext.update(...)` on
            # whatever web_login returns, assuming it's always a rendered
            # template response (which Odoo's own request.render() tags
            # with a `.qcontext` dict). A plain redirect response has no
            # such attribute, which crashed auth_signup with
            # "AttributeError: 'Response' object has no attribute
            # 'qcontext'" (seen as a 500 in the logs, which the proxy then
            # turned into a confusing "page not found"). Giving the
            # redirect an empty qcontext dict satisfies that blind
            # post-processing without changing our actual behavior.
            otp_redirect.qcontext = {}
            return otp_redirect

    return response


# Defensive: explicitly re-attach the routing metadata onto our patched
# function, in case functools.wraps' __dict__ merge didn't carry it over
# (depends on exactly how @http.route() is implemented in this Odoo
# version). Without this, /web/login silently 404s.
if hasattr(_original_web_login, 'routing'):
    _patched_web_login.routing = _original_web_login.routing
if hasattr(_original_web_login, 'original_func'):
    _patched_web_login.original_func = _original_web_login.original_func

Home.web_login = _patched_web_login
=======

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
>>>>>>> 8eaa44d131a3b00836da08466aa633a14b720292


class SMSOTPVerify(http.Controller):

<<<<<<< HEAD
    @http.route('/web/login/sms_otp', type='http', auth='none', methods=['GET', 'POST'], website=False, csrf=True)
    def sms_otp_verify(self, **kw):
        pending_uid = request.session.get(SESSION_PENDING_KEY)
        if not pending_uid:
            return werkzeug.utils.redirect('/web/login')

        user = request.env['res.users'].sudo().browse(pending_uid)
        error = None
=======
    @http.route('/web/login/sms_otp', type='http', auth='none', sitemap=False, csrf=True)
    def web_login_sms_otp(self, redirect=None, **kw):
        pending_uid = request.session.get(SESSION_PENDING_KEY)
        if not pending_uid:
            return request.redirect('/web/login')

        error = None
        user = request.env['res.users'].sudo().browse(pending_uid)
>>>>>>> 8eaa44d131a3b00836da08466aa633a14b720292

        if request.httprequest.method == 'POST':
            if kw.get('resend'):
                user._generate_and_send_sms_otp()
<<<<<<< HEAD
                error = "A new OTP has been sent."
=======
                error = 'A new OTP has been sent.'
>>>>>>> 8eaa44d131a3b00836da08466aa633a14b720292
            else:
                otp_input = kw.get('otp', '')
                if user._verify_sms_otp(otp_input):
                    user._clear_sms_otp()
                    request.session.pop(SESSION_PENDING_KEY, None)

<<<<<<< HEAD
                    # Finalize the real Odoo session now that OTP is verified.
                    request.session.uid = pending_uid
                    request.session.login = user.login
                    request.session.session_token = user._compute_session_token(request.session.sid)
                    request.update_env(user=pending_uid)

                    _logger.warning("SMS_OTP_DEBUG: OTP verified, finalizing login for uid=%s", pending_uid)
                    return werkzeug.utils.redirect('/web')
                else:
                    error = "Invalid or expired OTP. Please try again."

        return request.render('sms_otp_login.otp_form', {'error': error})
=======
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
>>>>>>> 8eaa44d131a3b00836da08466aa633a14b720292
