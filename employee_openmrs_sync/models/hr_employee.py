from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import json
import random
import string
import urllib3
import logging
import re
from requests.auth import HTTPBasicAuth
_logger = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import os


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    openmrs_user_uuid = fields.Char(
        string="OpenMRS User UUID",
        copy=False,
        readonly=True
    )

    openmrs_password = fields.Char(
        string="OpenMRS Password",
        copy=False,
        readonly=True
    )

    openmrs_sync_date = fields.Datetime(
        string="OpenMRS Sync Date",
        readonly=True
    )

    openmrs_sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed')
    ], default='pending', string="Sync Status", copy=False)

    openmrs_error = fields.Text(
        string="OpenMRS Error",
        readonly=True
    )

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------

    @api.model
    def create(self, vals):
        employee = super(HrEmployee, self).create(vals)
        employee._create_openmrs_user()
        return employee

    # ---------------------------------------------------------
    # WRITE
    # ---------------------------------------------------------

    def write(self, vals):

        # Store employees that are active before write
        employees_to_archive = self.filtered(lambda emp: emp.active)

        res = super(HrEmployee, self).write(vals)

        trigger_fields = [
            'user_id',
            'ohc_id',
            'job_id',
            'gender',
            'name',
            'mobile_phone',     # re-sync when Work Mobile changes
        ]

        # Existing OpenMRS Sync Logic
        if any(field in vals for field in trigger_fields):

            for employee in self:

                # Related User is mandatory
                if not employee.user_id:
                    continue

                # No OHC mapped
                if not employee.ohc_id:
                    continue

                # First time -> Create User (or link to the existing one)
                if not employee.openmrs_user_uuid:
                    employee._create_openmrs_user()

                # Existing User -> Update Locations
                else:
                    employee._update_openmrs_locations()

        # Archive Employee -> Delete User & Provider from OpenMRS
        if vals.get('active') is False:

            for employee in employees_to_archive:
                employee._delete_openmrs_user_provider()

        return res

    def _delete_openmrs_user_provider(self):
        self.ensure_one()

        api = self.env['openmrs.api']

        # Delete OpenMRS User
        if self.openmrs_user_uuid:
            api.delete_user(self.openmrs_user_uuid)

        # Delete OpenMRS Provider
        # if self.openmrs_provider_uuid:
        #     api.delete_provider(self.openmrs_provider_uuid)

    # ---------------------------------------------------------
    # HELPERS: REST BASE URL + EXISTING USER LOOKUP
    # ---------------------------------------------------------

    def _openmrs_rest_base_url(self):
        """
        REST base, e.g. https://host/openmrs/ws/rest/v1
        Uses 'openmrs_base_url' if set, otherwise derives it from
        'openmrs_location_create_url' (.../ws/rest/v1/location).
        """
        config = self.env['ir.config_parameter'].sudo()

        base_url = (config.get_param('openmrs_base_url') or "").rstrip('/')
        if base_url:
            return base_url

        location_url = (config.get_param('openmrs_location_create_url') or "").rstrip('/')
        if location_url.endswith('/location'):
            return location_url[:-len('/location')]

        return ""

    def _find_openmrs_user(self, username, system_id=None):
        """
        Look for an existing OpenMRS user by username (then by system id).
        Returns the user dict {uuid, username, systemId, userProperties}
        or False. Never raises.
        """
        base_url = self._openmrs_rest_base_url()
        if not base_url:
            _logger.warning("OpenMRS user lookup skipped: REST base URL not configured.")
            return False

        auth = HTTPBasicAuth(
            os.getenv("OPENMRS_USERNAME"),
            os.getenv("OPENMRS_PASSWORD")
        )

        for term in [username, system_id]:

            if not term:
                continue

            try:
                r = requests.get(
                    f"{base_url}/user",
                    params={
                        "q": term,
                        "v": "custom:(uuid,username,systemId,userProperties)"
                    },
                    auth=auth,
                    headers={"Accept": "application/json"},
                    verify=False,
                    timeout=30,
                )
                r.raise_for_status()

                for u in r.json().get("results", []):

                    if (u.get("username") or "").lower() == (username or "").lower():
                        return u

                    if system_id and (u.get("systemId") or "").lower() == system_id.lower():
                        return u

            except Exception as e:
                _logger.warning("OpenMRS user lookup failed for %s: %s", term, e)

        return False

    # ---------------------------------------------------------
    # MAIN METHOD
    # ---------------------------------------------------------

    def _create_openmrs_user(self):

        self.ensure_one()

        self._check_openmrs_server()

        # Already synced
        if self.openmrs_user_uuid:
            return

        # Related user mandatory
        if not self.user_id:
            return

        # OHC mandatory
        if not self.ohc_id:
            return

        # Login mandatory
        if not self.user_id.login:
            raise UserError(
                "Selected Related User does not have Login."
            )

        # Email mandatory
        system_id = self.user_id.email or self.work_email

        if not system_id:
            raise UserError(
                "Email is mandatory for OpenMRS User creation."
            )

        # First OHC
        ohc = self.ohc_id[0]

        if not ohc.location_uuid:
            raise UserError(
                "OpenMRS Location UUID is missing on OHC : %s"
                % ohc.name
            )

        # ---------------------------------------------------------
        # USER ALREADY EXISTS IN OPENMRS ?  -> link + assign OHC
        # ---------------------------------------------------------

        username = (self.user_id.name or "").replace(" ", "")

        existing_user = self._find_openmrs_user(username, system_id)

        if existing_user:

            _logger.info(
                "OpenMRS user %s already exists (%s) - linking and "
                "assigning OHC locations instead of creating.",
                username, existing_user["uuid"]
            )

            self.write({
                'openmrs_user_uuid': existing_user["uuid"],
            })

            if self.user_id:
                self.user_id.sudo().write({
                    'clinical_user': True
                })

            return self._update_openmrs_locations(
                merge_existing=True,
                existing_user=existing_user,
            )

        # ---------------------------------------------------------
        # CONFIG PARAMETERS
        # ---------------------------------------------------------

        config = self.env['ir.config_parameter'].sudo()

        api_url = config.get_param(
            'openmrs_user_create_url'
        )

        doctor_roles = config.get_param(
            'openmrs_doctor_roles'
        )

        nurse_roles = config.get_param(
            'openmrs_nurse_roles'
        )

        _logger.info("API URL = %s", api_url)
        _logger.info("Doctor Roles = %s", doctor_roles)
        _logger.info("Nurse Roles = %s", nurse_roles)

        if not api_url:
            raise UserError(
                "System Parameter 'openmrs_user_create_url' not configured."
            )

        if not doctor_roles:
            raise UserError(
                "Doctor Roles UUID not configured."
            )

        if not nurse_roles:
            raise UserError(
                "Nurse Roles UUID not configured."
            )

        # ---------------------------------------------------------
        # PASSWORD
        # ---------------------------------------------------------

        password = self._generate_random_password()
        location_uuids = self.ohc_id.mapped('location_uuid')

        # Remove empty values
        location_uuids = [uuid.strip() for uuid in location_uuids if uuid]

        if not location_uuids:
            raise UserError("Location UUID is not configured for the selected OHC(s).")

        # Convert to comma-separated string
        locations = ",".join(location_uuids)

        # ---------------------------------------------------------
        # NAME
        # ---------------------------------------------------------

        employee_name = (self.name or "").strip()

        _logger.info("Employee Name : %s", employee_name)

        name_parts = employee_name.split()

        _logger.info("Name Parts : %s", name_parts)

        given_name = name_parts[0] if len(name_parts) else ""

        family_name = ""

        if len(name_parts) > 1:
            family_name = " ".join(name_parts[1:])

        # ---------------------------------------------------------
        # GENDER
        # ---------------------------------------------------------

        gender = "O"

        if self.gender == "male":
            gender = "M"

        elif self.gender == "female":
            gender = "F"

        elif self.gender == "other":
            gender = "O"

        # ---------------------------------------------------------
        # ROLES
        # ---------------------------------------------------------

        job_name = ""

        if self.job_id:
            job_name = self.job_id.name.lower()

        if "doctor" in job_name:
            roles = doctor_roles
        else:
            roles = nurse_roles

        # ---------------------------------------------------------
        # PAYLOAD
        # ---------------------------------------------------------

        payload = {
            "username": username,
            "password": password,
            "systemId": system_id,
            "person": {
                "givenName": given_name,
                "familyName": family_name
            },
            "gender": gender,
            "roles": roles,
            "locations": locations
        }

        openmrs_user = os.getenv("OPENMRS_USERNAME")
        openmrs_password = os.getenv("OPENMRS_PASSWORD")

        if not openmrs_user or not openmrs_password:
            raise UserError("OpenMRS credentials are missing from the environment.")

        try:

            _logger.info("========== OpenMRS Payload ==========")
            _logger.info(json.dumps(
                dict(payload, password="********"), indent=4))
            _logger.info("=====================================")

            response = requests.post(
                api_url,
                json=payload,
                auth=HTTPBasicAuth(openmrs_user, openmrs_password),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json;charset=UTF-8",
                },
                verify=False,
                timeout=60,
            )

            if response.status_code in [200, 201, 202]:

                response_json = {}

                try:
                    response_json = response.json()
                except Exception:
                    response_json = {}

                user_uuid = (
                    response_json.get("uuid")
                    or response_json.get("userUuid")
                    or response_json.get("providerUuid")
                    or ""
                )

                self.write({
                    'openmrs_user_uuid': user_uuid,
                    'openmrs_password': password,
                    'openmrs_sync_status': 'success',
                    'openmrs_sync_date': fields.Datetime.now(),
                    'openmrs_error': False
                })

                # push Work Mobile to OpenMRS (never raises)
                self._sync_openmrs_phone(user_uuid)

                self._send_openmrs_credentials_email()

                if self.user_id:
                    self.user_id.sudo().write({
                        'clinical_user': True
                    })

                self.message_post(
                    body="""
                <b>Clinical User Created Successfully</b><br/>
                Username : %s<br/>
                Email : %s<br/>
                Password : %s<br/>
                Location : %s
                                    """ % (
                                        self.user_id.login,
                                        system_id,
                                        password,
                                        ohc.name
                                    )
                                )

                return True

            elif response.status_code == 400:

                error_message = response.text

                try:
                    error_json = response.json()

                    if error_json.get("error"):

                        error_message = error_json["error"].get(
                            "detail",
                            error_json["error"].get("message")
                        )

                except Exception:
                    pass

                self.write({
                    'openmrs_sync_status': 'failed',
                    'openmrs_error': error_message
                })

                raise UserError(error_message)

            else:

                self.write({
                    'openmrs_sync_status': 'failed',
                    'openmrs_error': response.text
                })

                raise UserError(
                    "OpenMRS Error\n\nStatus Code : %s\n\n%s"
                    % (
                        response.status_code,
                        response.text
                    )
                )

        except Exception as e:

            self.write({
                'openmrs_sync_status': 'failed',
                'openmrs_error': str(e)
            })

            raise UserError(
                "Error while creating OpenMRS User\n\n%s"
                % str(e)
            )

    def _generate_random_password(self):
        """
        Generates password like:
        Admin123@
        Pritee456@
        Doctor789@
        """

        # First character - Uppercase
        first_char = random.choice(string.ascii_uppercase)

        # Next 5 lowercase letters
        lowercase = ''.join(random.choices(string.ascii_lowercase, k=5))

        # Next 3 digits
        digits = ''.join(random.choices(string.digits, k=3))

        # Fixed special character
        special = "@"

        return first_char + lowercase + digits + special

    def _update_openmrs_locations(self, merge_existing=False, existing_user=None):
        """
        Push the employee's OHC locations to the OpenMRS user.

        merge_existing=True is used when we just linked to a user that
        already existed in OpenMRS: the locations that user already has
        are kept and the Odoo OHC locations are added to them.
        """

        self.ensure_one()
        self._check_openmrs_server()

        api_url = self.env['ir.config_parameter'].sudo().get_param(
            'openmrs_user_create_url'
        )

        employee_name = (self.name or "").strip()
        name_parts = employee_name.split()

        given_name = name_parts[0] if len(name_parts) else ""
        family_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        username = (self.user_id.name or "").replace(" ", "")

        system_id = self.user_id.email or self.user_id.login

        gender_map = {
            "male": "M",
            "female": "F",
            "other": "O",
        }

        gender = gender_map.get(self.gender or "", "O")

        config = self.env['ir.config_parameter'].sudo()

        doctor_roles = config.get_param('openmrs_doctor_roles')
        nurse_roles = config.get_param('openmrs_nurse_roles')

        job_name = ""

        if self.job_id:
            job_name = self.job_id.name.lower()

        if "doctor" in job_name:
            roles = doctor_roles
        else:
            roles = nurse_roles

        # All OHC UUIDs
        location_uuids = []

        for ohc in self.ohc_id:
            if ohc.location_uuid:
                location_uuids.append(ohc.location_uuid.strip())

        # Keep the locations the existing OpenMRS user already had
        if merge_existing and existing_user:
            props = existing_user.get("userProperties") or {}
            for uuid in (props.get("locations") or "").split(","):
                uuid = uuid.strip()
                if uuid and uuid not in location_uuids:
                    location_uuids.append(uuid)

        locations = ",".join(location_uuids)

        payload = {
            "userUuid": self.openmrs_user_uuid,
            "username": username,
            "systemId": system_id,
            "person": {
                "givenName": given_name,
                "familyName": family_name
            },
            "gender": gender,
            "roles": roles,
            "locations": locations
        }

        # Only send a password when we really know it (users created by
        # Odoo). For a user that already existed in OpenMRS we do NOT
        # send one, so their current password is not overwritten.
        if self.openmrs_password:
            payload["password"] = self.openmrs_password

        _logger.info("========== OpenMRS Update Payload ==========")
        _logger.info(json.dumps(
            dict(payload, **({"password": "********"} if "password" in payload else {})),
            indent=4))

        openmrs_user = os.getenv("OPENMRS_USERNAME")
        openmrs_password = os.getenv("OPENMRS_PASSWORD")

        if not openmrs_user or not openmrs_password:
            raise UserError("OpenMRS credentials are missing from the environment.")

        response = requests.post(
            api_url,
            json=payload,
            auth=HTTPBasicAuth(openmrs_user, openmrs_password),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json;charset=UTF-8",
            },
            verify=False,
            timeout=60,
        )

        _logger.info("Status Code : %s", response.status_code)
        _logger.info("Response : %s", response.text)

        if response.status_code in [200, 201]:

            self.write({
                'openmrs_sync_status': 'success',
                'openmrs_sync_date': fields.Datetime.now(),
                'openmrs_error': False
            })

            # push Work Mobile to OpenMRS (never raises)
            self._sync_openmrs_phone(self.openmrs_user_uuid)

            self.message_post(
                body="""
                <b>Clinical User %s Successfully</b><br/>
                Username : %s<br/>
                Locations : %s
                """ % (
                    "Linked and Updated" if merge_existing else "Updated",
                    username,
                    ", ".join(self.ohc_id.mapped('name')),
                )
            )

            return True

        self.write({
            'openmrs_sync_status': 'failed',
            'openmrs_error': response.text
        })

        raise UserError(
            "Unable to update OpenMRS User\n\n%s" % response.text
        )

    def _send_openmrs_credentials_email(self):
        self.ensure_one()

        if not self.user_id.email:
            return
        username = (self.user_id.name or "").replace(" ", "")

        base_url = self.env['ir.config_parameter'].sudo().get_param('openmrs.login_url')
        if not base_url:
            raise UserError("OpenMRS login URL is not configured in System Parameters.")

        mail_values = {
            'subject': 'Your OpenMRS Login Credentials',
            'email_to': self.user_id.email,
            'body_html': f"""
                <p>Hello {self.name},</p>

                <p>Your OpenMRS account has been created successfully.</p>

                <p><b>Username:</b> {username}</p>

                <p><b>Password:</b> {self.openmrs_password}</p>

                <p>
                    <a href="{base_url}">
                        Login to Clinical
                    </a>
                </p>

                <p>Thank You !!</p>
            """,
        }

        mail = self.env['mail.mail'].create(mail_values)
        mail.send()

    def _check_openmrs_server(self):

        api_url = self.env['ir.config_parameter'].sudo().get_param(
            'openmrs_user_create_url'
        )

        if not api_url:
            raise UserError(
                "OpenMRS URL is not configured."
            )

        openmrs_user = os.getenv("OPENMRS_USERNAME")
        openmrs_password = os.getenv("OPENMRS_PASSWORD")

        if not openmrs_user or not openmrs_password:
            raise UserError("OpenMRS credentials are missing from the environment.")

        try:
            response = requests.options(
                api_url,
                auth=HTTPBasicAuth(openmrs_user, openmrs_password),
                timeout=10,
                verify=False,
            )

            if response.status_code not in (200, 201, 202, 400, 401, 403, 405):
                raise UserError(
                    "Clinical server is currently unavailable. Please try again later."
                )

        except requests.exceptions.ConnectTimeout:
            raise UserError(
                "Clinical server is not responding."
            )

        except requests.exceptions.ConnectionError:
            raise UserError(
                "Clinical server is currently down."
            )

        except requests.exceptions.RequestException as e:
            raise UserError(
                "Unable to connect to Clinical Server.\n\n%s" % str(e)
            )

    # ---------------------------------------------------------
    # PHONE SYNC  (Odoo Work Mobile -> OpenMRS person attribute)
    # ---------------------------------------------------------

    def _sync_openmrs_phone(self, user_uuid):
        """
        Push hr.employee.mobile_phone to the OpenMRS 'phoneNumber'
        person attribute (shown in Manage Person).
        Never raises: a phone problem must not roll back the user
        that was already created/updated in OpenMRS.
        """
        self.ensure_one()

        try:
            # Keep digits only, last 10 (drops +91, spaces, dashes)
            phone = re.sub(r'\D', '', self.mobile_phone or "")[-10:]
            if not phone or not user_uuid:
                return

            config = self.env['ir.config_parameter'].sudo()
            base_url = (config.get_param('openmrs_base_url') or "").rstrip('/')
            attr_type_uuid = config.get_param('openmrs_phone_attribute_uuid')

            if not base_url or not attr_type_uuid:
                _logger.warning(
                    "OpenMRS phone sync skipped: set system parameters "
                    "'openmrs_base_url' and 'openmrs_phone_attribute_uuid'."
                )
                return

            openmrs_user = os.getenv("OPENMRS_USERNAME")
            openmrs_password = os.getenv("OPENMRS_PASSWORD")
            auth = HTTPBasicAuth(openmrs_user, openmrs_password)
            headers = {"Accept": "application/json", "Content-Type": "application/json"}

            # 1. user -> person uuid
            r = requests.get(
                f"{base_url}/user/{user_uuid}?v=custom:(person:(uuid))",
                auth=auth, headers=headers, verify=False, timeout=30)
            r.raise_for_status()
            person_uuid = r.json()["person"]["uuid"]

            # 2. existing phone attribute (update instead of duplicating)
            r = requests.get(
                f"{base_url}/person/{person_uuid}/attribute?v=custom:(uuid,attributeType:(uuid))",
                auth=auth, headers=headers, verify=False, timeout=30)
            r.raise_for_status()
            existing = next(
                (a for a in r.json().get("results", [])
                 if a["attributeType"]["uuid"] == attr_type_uuid),
                None)

            body = {"attributeType": attr_type_uuid, "value": phone}
            url = f"{base_url}/person/{person_uuid}/attribute"
            if existing:
                url += f"/{existing['uuid']}"       # POST here updates it

            r = requests.post(url, json=body, auth=auth, headers=headers,
                              verify=False, timeout=30)
            if r.status_code in (200, 201):
                _logger.info("OpenMRS phone synced for %s", self.name)
            else:
                _logger.error("Phone sync failed: %s %s", r.status_code, r.text)

        except Exception as e:
            _logger.error("OpenMRS phone sync error for %s: %s", self.name, e)
