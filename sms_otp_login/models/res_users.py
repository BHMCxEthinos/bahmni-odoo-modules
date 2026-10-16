<<<<<<< HEAD
# -*- coding: utf-8 -*-
=======
>>>>>>> 8eaa44d131a3b00836da08466aa633a14b720292
import hashlib
import logging
import os
import random
<<<<<<< HEAD
import re
from datetime import timedelta
=======
from datetime import datetime, timedelta
>>>>>>> 8eaa44d131a3b00836da08466aa633a14b720292

import requests

from odoo import fields, models
<<<<<<< HEAD
from odoo.fields import Datetime
=======
from odoo.exceptions import UserError
>>>>>>> 8eaa44d131a3b00836da08466aa633a14b720292

_logger = logging.getLogger(__name__)

OTP_VALID_MINUTES = 5
OTP_LENGTH = 6

<<<<<<< HEAD
# ---------------------------------------------------------------------
# Nettyfish (retailsms.nettyfish.com) configuration - ALL from env vars.
# No Odoo System Parameters are used anywhere in this module, as requested.
# ---------------------------------------------------------------------
NETTY_API_URL = os.environ.get("NETTY_API_URL", "http://retailsms.nettyfish.com/api/mt/SendSMS")
NETTY_USER = os.environ.get("NETTY_USER", "")
NETTY_PASSWORD = os.environ.get("NETTY_PASSWORD", "")
NETTY_SENDERID = os.environ.get("NETTY_SENDERID", "")
NETTY_ROUTE = os.environ.get("NETTY_ROUTE", "4")
NETTY_CHANNEL = os.environ.get("NETTY_CHANNEL", "Trans")
NETTY_PEID = os.environ.get("NETTY_PEID", "")
NETTY_DLT_TEMPLATE_ID = os.environ.get("NETTY_DLT_TEMPLATE_ID", "")

# ---------------------------------------------------------------------
# SECURITY: client requires that OTPs and credentials NEVER appear in
# server logs or audit trails, under any configuration. There is
# deliberately no env var / debug flag anywhere in this file that can
# make it print an OTP, a password, or a raw provider request/response -
# that capability has been removed from the code entirely, not just
# turned off by default, so it cannot be re-enabled by a config change.
#
# We also defensively silence urllib3/requests' own internal loggers,
# so that even if someone raises Odoo's root log level to DEBUG later,
# the underlying HTTP library won't print the request URL (which
# contains the Nettyfish user/password as query parameters).
# ---------------------------------------------------------------------
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

=======
>>>>>>> 8eaa44d131a3b00836da08466aa633a14b720292

class ResUsers(models.Model):
    _inherit = 'res.users'

    otp_mobile_number = fields.Char(
<<<<<<< HEAD
        string="OTP Mobile Number",
        help="Mobile number (with country code, e.g. +919372914050) that "
             "receives the SMS OTP at every login. Leave empty to disable "
             "SMS OTP for this user.",
    )
    sms_otp_hash = fields.Char(string="SMS OTP Hash", copy=False)
    sms_otp_expiry = fields.Datetime(string="SMS OTP Expiry", copy=False)

    def _generate_and_send_sms_otp(self):
        self.ensure_one()
        otp = ''.join(random.choices('0123456789', k=OTP_LENGTH))
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        expiry = Datetime.now() + timedelta(minutes=OTP_VALID_MINUTES)

        self.sudo().write({
            'sms_otp_hash': otp_hash,
            'sms_otp_expiry': expiry,
        })

        # NOTE: deliberately no logging of `otp` anywhere in this method.
        # Only the SHA-256 hash is ever persisted (on the user record,
        # not in a log file), and that hash cannot be reversed to the
        # original 6-digit code.
        _logger.info("SMS_OTP: OTP generated for user '%s', sending via SMS.", self.login)

        message = "Your OTP %s to login into Bharath Medicare app." % (otp,)
        self._send_sms_via_netty(self.otp_mobile_number, message)

    def _verify_sms_otp(self, otp_input):
        self.ensure_one()
        if not self.sms_otp_hash or not self.sms_otp_expiry:
            return False
        if Datetime.now() > self.sms_otp_expiry:
=======
        string='OTP Mobile Number',
        help="Mobile number in E.164 format (e.g. +919999999999). "
             "Required for SMS OTP login to work for this user.",
    )
    sms_otp_hash = fields.Char(string='OTP Hash', copy=False)
    sms_otp_expiry = fields.Datetime(string='OTP Expiry', copy=False)

    # ------------------------------------------------------------------
    # OTP lifecycle
    # ------------------------------------------------------------------
    def _generate_and_send_sms_otp(self):
        """Generate a fresh OTP, store its hash, and SMS it to the user."""
        self.ensure_one()
        if not self.otp_mobile_number:
            raise UserError(
                "No mobile number is configured for SMS OTP login on this "
                "account. Contact your administrator."
            )

        otp = ''.join(random.choices('0123456789', k=OTP_LENGTH))
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()

        self.sudo().write({
            'sms_otp_hash': otp_hash,
            'sms_otp_expiry': fields.Datetime.to_string(
                datetime.now() + timedelta(minutes=OTP_VALID_MINUTES)
            ),
        })

        message = (
            "Your login OTP is %s. It is valid for %s minutes. "
            "Do not share this code with anyone." % (otp, OTP_VALID_MINUTES)
        )

        debug_log = str(os.environ.get('OTP_DEBUG_LOG', '')).lower() in ('1', 'true', 'yes')

        if debug_log:
            _logger.warning(
                "SMS OTP DEBUG MODE: OTP for user '%s' (mobile %s) is %s. "
                "REMOVE the OTP_DEBUG_LOG env var before going to "
                "production - logging OTPs defeats the purpose of 2FA.",
                self.login, self.otp_mobile_number, otp,
            )

        try:
            self._send_sms_via_netty(self.otp_mobile_number, message)
        except UserError:
            if debug_log:
                # Debug mode: don't block login just because SMS delivery
                # failed - the code is already in the server log above.
                _logger.warning(
                    "SMS OTP: send failed but debug mode is on, continuing "
                    "without blocking login."
                )
            else:
                raise
        return True

    def _verify_sms_otp(self, otp_input):
        """Return True if otp_input matches the stored (unexpired) OTP."""
        self.ensure_one()
        if not self.sms_otp_hash or not self.sms_otp_expiry:
            return False
        if fields.Datetime.from_string(self.sms_otp_expiry) < datetime.now():
>>>>>>> 8eaa44d131a3b00836da08466aa633a14b720292
            return False
        candidate = hashlib.sha256((otp_input or '').strip().encode()).hexdigest()
        return candidate == self.sms_otp_hash

    def _clear_sms_otp(self):
<<<<<<< HEAD
        self.ensure_one()
        self.sudo().write({
            'sms_otp_hash': False,
            'sms_otp_expiry': False,
        })

    def _send_sms_via_netty(self, mobile_number, message):
        if not mobile_number:
            _logger.warning("SMS_OTP: no mobile number set on user, cannot send OTP SMS.")
            return
        number = mobile_number.lstrip('+')
        params = {
            'user': NETTY_USER,
            'password': NETTY_PASSWORD,
            'senderid': NETTY_SENDERID,
            'channel': NETTY_CHANNEL,
=======
        self.sudo().write({'sms_otp_hash': False, 'sms_otp_expiry': False})

    # ------------------------------------------------------------------
    # Nettyfish (retailsms.nettyfish.com) integration
    # ------------------------------------------------------------------
    def _send_sms_via_netty(self, mobile_number, message):
        """Sends via Nettyfish - simple GET-based HTTP API, common for
        Indian DLT-compliant bulk SMS providers.

        Set these environment variables on the odoo container
        (docker-compose.yml, under the odoo service's `environment:`):
          NETTY_USER       - your Nettyfish username
          NETTY_PASSWORD   - your Nettyfish password
          NETTY_SENDERID   - your approved sender ID
          NETTY_ROUTE      - your route ID (ask your Nettyfish account
                              contact for the OTP/transactional route,
                              NOT promo)
          NETTY_CHANNEL    - defaults to 'Trans' (transactional).
                              Promotional routes often cannot reach
                              DND-registered numbers.
          NETTY_API_URL    - defaults to
                              http://retailsms.nettyfish.com/api/mt/SendSMS
        """
        api_url = os.environ.get('NETTY_API_URL', 'http://retailsms.nettyfish.com/api/mt/SendSMS')
        user = os.environ.get('NETTY_USER', '')
        password = os.environ.get('NETTY_PASSWORD', '')
        senderid = os.environ.get('NETTY_SENDERID', '')
        route = os.environ.get('NETTY_ROUTE', '')
        channel = os.environ.get('NETTY_CHANNEL', 'Trans')

        if not (user and password and senderid and route):
            _logger.error(
                "SMS OTP: Nettyfish credentials incomplete. Set NETTY_USER, "
                "NETTY_PASSWORD, NETTY_SENDERID, NETTY_ROUTE as environment "
                "variables on the odoo container (docker-compose.yml)."
            )
            raise UserError(
                "SMS provider is not configured. Contact your administrator."
            )

        # Nettyfish wants the number without a leading '+'
        number = mobile_number.lstrip('+')

        params = {
            'user': user,
            'password': password,
            'senderid': senderid,
            'channel': channel,
>>>>>>> 8eaa44d131a3b00836da08466aa633a14b720292
            'DCS': '0',
            'flashsms': '0',
            'number': number,
            'text': message,
<<<<<<< HEAD
            'route': NETTY_ROUTE,
            'peid': NETTY_PEID,
            'dlttemplateid': NETTY_DLT_TEMPLATE_ID,
        }
        # SECURITY: we never log the request URL (it contains
        # NETTY_USER/NETTY_PASSWORD as query params) and never raw
        # exception text (a requests.ConnectionError's own message embeds
        # the full request URL, credentials included).
        #
        # We DO log Nettyfish's response body, because a 200 OK from their
        # API only means "we received your request" - not "we accepted
        # and queued the SMS". Nettyfish puts the real accept/reject
        # reason (e.g. invalid sender id, DND block, wrong route) in the
        # response body, and without seeing it we can't diagnose delivery
        # failures. To keep the "no OTP in logs" rule intact, every run of
        # 4+ digits (long enough to be our 6-digit OTP, never part of a
        # status word) is redacted before logging - the OTP itself can
        # never reach the log, only the surrounding status text can.
        try:
            resp = requests.get(NETTY_API_URL, params=params, timeout=10)
            ok = resp.ok
            safe_body = re.sub(r'\d{4,}', '[REDACTED]', resp.text or '')
            _logger.info(
                "SMS_OTP: Nettyfish request completed, http_status=%s, ok=%s, body=%s",
                resp.status_code, ok, safe_body,
            )
            resp.raise_for_status()
        except Exception as exc:
            _logger.error("SMS_OTP: failed to send OTP SMS via Nettyfish (%s)", type(exc).__name__)
=======
            'route': route,
        }

        try:
            resp = requests.get(api_url, params=params, timeout=10)
            _logger.warning(
                "SMS_OTP_DEBUG: Nettyfish responded status=%s body=%s",
                resp.status_code, resp.text,
            )
            resp.raise_for_status()
        except requests.RequestException:
            _logger.exception("SMS OTP: failed to send SMS via Nettyfish")
            raise UserError(
                "Failed to send the OTP SMS. Please try again or contact "
                "your administrator."
            )
>>>>>>> 8eaa44d131a3b00836da08466aa633a14b720292
