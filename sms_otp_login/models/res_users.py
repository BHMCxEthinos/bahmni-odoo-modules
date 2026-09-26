import hashlib
import logging
import os
import random
from datetime import datetime, timedelta

import requests

from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

OTP_VALID_MINUTES = 5
OTP_LENGTH = 6


class ResUsers(models.Model):
    _inherit = 'res.users'

    otp_mobile_number = fields.Char(
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
            return False
        candidate = hashlib.sha256((otp_input or '').strip().encode()).hexdigest()
        return candidate == self.sms_otp_hash

    def _clear_sms_otp(self):
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
            'DCS': '0',
            'flashsms': '0',
            'number': number,
            'text': message,
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
