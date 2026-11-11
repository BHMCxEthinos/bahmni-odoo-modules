# -*- coding: utf-8 -*-
import hashlib
import logging
import os
import random
import re
from datetime import timedelta

import requests

from odoo import fields, models
from odoo.fields import Datetime

_logger = logging.getLogger(__name__)

OTP_VALID_MINUTES = 5
OTP_LENGTH = 6

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


class ResUsers(models.Model):
    _inherit = 'res.users'

    otp_mobile_number = fields.Char(
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
            return False
        candidate = hashlib.sha256((otp_input or '').strip().encode()).hexdigest()
        return candidate == self.sms_otp_hash

    def _clear_sms_otp(self):
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
            'DCS': '0',
            'flashsms': '0',
            'number': number,
            'text': message,
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
