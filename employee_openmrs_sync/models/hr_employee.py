from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import json
import random
import string
import urllib3
import logging
from requests.auth import HTTPBasicAuth
_logger = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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

    # def write(self, vals):

    #     res = super(HrEmployee, self).write(vals)

    #     trigger_fields = [
    #         'user_id',
    #         'ohc_id',
    #         'job_id',
    #         'gender',
    #         'name'
    #     ]

    #     if any(field in vals for field in trigger_fields):
    #         for employee in self:
    #             employee._create_openmrs_user()

    #     return res

    # def write(self, vals):

    #     res = super(HrEmployee, self).write(vals)

    #     trigger_fields = [
    #         'user_id',
    #         'ohc_id',
    #         'job_id',
    #         'gender',
    #         'name'
    #     ]

    #     if any(field in vals for field in trigger_fields):

    #         for employee in self:

               
    #             if not employee.user_id:
    #                 continue

               
    #             if not employee.ohc_id:
    #                 continue

               
    #             if not employee.openmrs_user_uuid:
    #                 employee._create_openmrs_user()

               
    #             else:
    #                 employee._update_openmrs_locations()

    #     return res
    def write(self, vals):

        # Store employees that are active before write
        employees_to_archive = self.filtered(lambda emp: emp.active)

        res = super(HrEmployee, self).write(vals)

        trigger_fields = [
            'user_id',
            'ohc_id',
            'job_id',
            'gender',
            'name'
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

                # First time -> Create User
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
        username = (self.user_id.name or "").replace(" ", "")
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

        # employee_name = (self.name or "").strip()

        # name_parts = employee_name.split()
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

    
        try:

            _logger.info("========== OpenMRS Payload ==========")
            _logger.info(json.dumps(payload, indent=4))
            _logger.info("=====================================")

        
            response = requests.post(
                api_url,
                json=payload,
                auth=HTTPBasicAuth("superman", "vA2WZasrRFE="),
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
    
    def _update_openmrs_locations(self):

        self.ensure_one()
        self._check_openmrs_server()

        api_url = self.env['ir.config_parameter'].sudo().get_param(
            'openmrs_user_create_url'
        )

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Basic U3VwZXJtYW46VHE2OEUwUGV9MjU2",
        }

    
        employee_name = (self.name or "").strip()
        name_parts = employee_name.split()

        given_name = name_parts[0] if len(name_parts) else ""
        family_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    
        username = (self.user_id.name or "").replace(" ", "")

   
        system_id = self.user_id.email or self.user_id.login
        # password = self._generate_random_password()
       
      
        gender_map = {
            "male": "M",
            "female": "F",
            "other": "O",
        }

        gender = gender_map.get(self.gender or "", "O")

        # Roles
        # roles = self.env['ir.config_parameter'].sudo().get_param(
        #     'employee_openmrs_sync.roles_uuid'
        # )
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

        locations = ",".join(location_uuids)

        payload = {
            "userUuid": self.openmrs_user_uuid,
            "username": username,
            "password": self.openmrs_password,
            "systemId": system_id,
            "person": {
                "givenName": given_name,
                "familyName": family_name
            },
            "gender": gender,
            "roles": roles,
            "locations": locations
        }

        _logger.info("========== OpenMRS Update Payload ==========")
        _logger.info(json.dumps(payload, indent=4))

        response = requests.post(
                api_url,
                json=payload,
                auth=HTTPBasicAuth("superman", "vA2WZasrRFE="),
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

            self.message_post(
                body="""
                <b>Clinical User Updated Successfully</b><br/>
                Username : %s<br/>
                Locations : %s<br/>
                Password: %s
                """ % (
                    username,
                    ", ".join(self.ohc_id.mapped('name')),
                self.openmrs_password)
            )

            return True

        raise UserError(
            "Unable to update OpenMRS User\n\n%s" % response.text
        )
    
    def _send_openmrs_credentials_email(self):
        self.ensure_one()

        if not self.user_id.email:
            return
        username = (self.user_id.name or "").replace(" ", "")

        mail_values = {
            'subject': 'Your OpenMRS Login Credentials',
            'email_to': self.user_id.email,
            'body_html': f"""
                <p>Hello {self.name},</p>

                <p>Your OpenMRS account has been created successfully.</p>

                <p><b>Username:</b> {username}</p>

                <p><b>Password:</b> {self.openmrs_password}</p>

                <p>
                    <a href="https://20.204.22.106">
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

        try:
            response = requests.options(
                api_url,
                auth=HTTPBasicAuth("superman", "vA2WZasrRFE="),
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