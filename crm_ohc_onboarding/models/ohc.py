import logging
import requests
import os
from requests.auth import HTTPBasicAuth
from odoo import models, fields,api,_
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

_logger.info("===== OHC PY FILE LOADED =====")

class OhcManagement(models.Model):
    _inherit = 'ohc.management'

    

    location_uuid = fields.Char(
    string="OpenMRS Location UUID"
    )

    def create_openmrs_location(self):

        self.ensure_one()

        customer = self.company_id

        # base_url = "https://20.204.22.106/openmrs/ws/rest/v1/location"

        username = "superman"
        password = "vA2WZasrRFE="
        # openmrs_username = os.getenv("OPENMRS_USERNAME")
        # openmrs_password = os.getenv("OPENMRS_PASSWORD")

        # if not openmrs_username or not openmrs_password:
        #     raise ValueError(
        #         "OPENMRS_USERNAME and OPENMRS_PASSWORD must be configured"
        #     )   

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
        }

    

        config = self.env['ir.config_parameter'].sudo()

        base_url= config.get_param('openmrs_location_create_url')

        FACILITY_TAG = config.get_param(
            'openmrs_facility_location_tag'
        )
        CUSTOMER_TAG=config.get_param('openmrs_customer_location_tag')

        LOGIN_TAG = config.get_param(
            'openmrs_login_location_tag'
        )

        VISIT_TAG = config.get_param(
            'openmrs_visit_location_tag'
        )

        OHC_ID_ATTRIBUTE = config.get_param(
            'openmrs_ohc_id_attribute_uuid'
        )

        CUSTOMER_CODE_ATTRIBUTE = config.get_param(
            'openmrs_customer_code_attribute_uuid'
        )
        BHARATH_CLINIC_UUID=config.get_param('openmrs_bharath_clinic_location_uuid')
        required = {
            "Facility Tag": FACILITY_TAG,
            "Login Tag": LOGIN_TAG,
            "Visit Tag": VISIT_TAG,
            "OHC ID Attribute": OHC_ID_ATTRIBUTE,
            "Customer Code Attribute": CUSTOMER_CODE_ATTRIBUTE,
        }

        for name, value in required.items():
            if not value:
                raise UserError(
                    _("%s System Parameter is not configured.") % name
        )

        

        search_response = requests.get(
            base_url,
            params={
                "v": "default",
                "q": customer.name,
            },
            auth=HTTPBasicAuth(username,password),
            headers=headers,
            verify=False,
            timeout=60,
        )

        search_response.raise_for_status()

        results = search_response.json().get("results", [])

        

        if results:

            parent_uuid = results[0]["uuid"]

            customer.write({
                "parent_location_uuid": parent_uuid
            })

            _logger.info(
                "Parent Location already exists : %s",
                parent_uuid
            )

       

        else:

            payload = {

                "name": customer.name,

                "description": customer.name,

                "tags": [

                    FACILITY_TAG,
                    CUSTOMER_TAG

                ],
                "parentLocation":  BHARATH_CLINIC_UUID

            }

            response = requests.post(
                base_url,
                json=payload,
                auth=HTTPBasicAuth(username, password),
                headers=headers,
                verify=False,
                timeout=60,
            )

            response.raise_for_status()

            parent_uuid = response.json()["uuid"]

            customer.write({
                "parent_location_uuid": parent_uuid
            })

            _logger.info(
                "Parent Location Created : %s",
                parent_uuid
            )

        
        payload = {

            "name": self.name,

            "description": self.name,

            "address1": "",

            "cityVillage": "",

            "stateProvince": "",

            "country": "",

            "postalCode": "",

            "countyDistrict": "",

            "tags": [

                LOGIN_TAG,

                VISIT_TAG

            ],

            "parentLocation": parent_uuid,

            "attributes": [

                {

                    "attributeType": OHC_ID_ATTRIBUTE,

                    "value": self.ohc_id

                },
                {
                    "attributeType": CUSTOMER_CODE_ATTRIBUTE,
                    "value": customer.customer_code or ""
                }

            ]

        }

        response = requests.post(
            base_url,
            json=payload,
            auth=HTTPBasicAuth(username, password),
            headers=headers,
            verify=False,
            timeout=60,
        )

        response.raise_for_status()

        location_uuid = response.json()["uuid"]

        self.write({

            "location_uuid": location_uuid

        })

        _logger.info(
            "OHC Location Created : %s",
            location_uuid
        )

    def sync_openmrs_location(self):
        """
        Synchronize OHC with OpenMRS.
        """
        self.ensure_one()

        if self.location_uuid:
            _logger.info(
                "OpenMRS location already synced."
            )
            return

        self.create_openmrs_location()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    parent_location_uuid = fields.Char(
    string="Parent Location UUID"
    )
