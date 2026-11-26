import logging
import os

import requests
from requests.auth import HTTPBasicAuth

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class OhcManagement(models.Model):
    _inherit = 'ohc.management'

    location_uuid = fields.Char(
        string="OpenMRS Location UUID"
    )

    # ---------------------------------------------------------
    # NO DUPLICATE OHC NAME (Odoo side)
    # ---------------------------------------------------------
    @api.constrains('name')
    def _check_unique_ohc_name(self):
        for rec in self:
            if not rec.name:
                continue
            duplicate = self.with_context(active_test=False).search([
                ('name', '=ilike', rec.name.strip()),
                ('id', '!=', rec.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    "OHC Name '%s' already exists. "
                    "Please enter a different OHC Name."
                ) % rec.name)

    # ---------------------------------------------------------
    # OPENMRS HELPERS
    # ---------------------------------------------------------
    @staticmethod
    def _openmrs_find_location(base_url, name, auth, headers):
        """
        Find a non-retired OpenMRS location by EXACT name
        (case-insensitive), wherever it sits in the hierarchy.
        OpenMRS does not allow two locations with the same name,
        so the name alone identifies it.
        Returns the location UUID or False.
        """
        response = requests.get(
            base_url,
            params={"v": "default", "q": name},
            auth=auth,
            headers=headers,
            verify=False,
            timeout=60,
        )
        response.raise_for_status()

        wanted = (name or "").strip().lower()
        for loc in response.json().get("results", []):
            if (loc.get("name") or "").strip().lower() == wanted:
                return loc["uuid"]
        return False

    @staticmethod
    def _openmrs_get_location(base_url, uuid, auth, headers):
        """
        Read one location with its parent. Returns the dict, or None
        if it does not exist.
        """
        response = requests.get(
            "%s/%s" % (base_url.rstrip("/"), uuid),
            params={"v": "custom:(uuid,name,retired,parentLocation:(uuid))"},
            auth=auth,
            headers=headers,
            verify=False,
            timeout=60,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _openmrs_post_location(base_url, payload, auth, headers, label="location"):
        _logger.info("OpenMRS POST (%s): %s", label, payload)
        response = requests.post(
            base_url,
            json=payload,
            auth=auth,
            headers=headers,
            verify=False,
            timeout=60,
        )
        if response.status_code not in (200, 201):
            raise UserError(_(
                "OpenMRS %s creation failed.\n\nStatus Code : %s\n\n"
                "Payload sent:\n%s\n\nResponse:\n%s"
            ) % (label, response.status_code, payload, response.text[:500]))
        return response.json()["uuid"]

    @staticmethod
    def _openmrs_set_parent(base_url, uuid, parent_uuid, auth, headers):
        """Attach an existing location to its parent."""
        response = requests.post(
            "%s/%s" % (base_url.rstrip("/"), uuid),
            json={"parentLocation": parent_uuid},
            auth=auth,
            headers=headers,
            verify=False,
            timeout=60,
        )
        if response.status_code not in (200, 201):
            raise UserError(_(
                "Could not set the parent location in OpenMRS.\n\n"
                "Status Code : %s\n\n%s"
            ) % (response.status_code, response.text[:500]))

    def _openmrs_ensure_parent(self, base_url, uuid, parent_uuid, auth, headers):
        """Make sure location `uuid` is a child of `parent_uuid`."""
        loc = self._openmrs_get_location(base_url, uuid, auth, headers) or {}
        current_parent = (loc.get("parentLocation") or {}).get("uuid")
        if current_parent != parent_uuid:
            _logger.info(
                "Fixing parent of location %s : %s -> %s",
                uuid, current_parent, parent_uuid,
            )
            self._openmrs_set_parent(base_url, uuid, parent_uuid, auth, headers)

    # ---------------------------------------------------------
    # MAIN: CREATE / LINK LOCATION
    # ---------------------------------------------------------
    def create_openmrs_location(self):

        self.ensure_one()

        customer = self.company_id

        openmrs_user = os.getenv("OPENMRS_USERNAME")
        openmrs_password = os.getenv("OPENMRS_PASSWORD")

        if not openmrs_user or not openmrs_password:
            raise UserError("OpenMRS credentials are missing from the environment.")

        auth = HTTPBasicAuth(openmrs_user, openmrs_password)

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
        }

        config = self.env['ir.config_parameter'].sudo()

        base_url = config.get_param('openmrs_location_create_url')
        FACILITY_TAG = config.get_param('openmrs_facility_location_tag')
        CUSTOMER_TAG = config.get_param('openmrs_customer_location_tag')
        LOGIN_TAG = config.get_param('openmrs_login_location_tag')
        VISIT_TAG = config.get_param('openmrs_visit_location_tag')
        OHC_ID_ATTRIBUTE = config.get_param('openmrs_ohc_id_attribute_uuid')
        CUSTOMER_CODE_ATTRIBUTE = config.get_param('openmrs_customer_code_attribute_uuid')
        BHARATH_CLINIC_UUID = config.get_param('openmrs_bharath_clinic_location_uuid')

        required = {
            "Location Create URL (openmrs_location_create_url)": base_url,
            "Facility Tag (openmrs_facility_location_tag)": FACILITY_TAG,
            "Customer Tag (openmrs_customer_location_tag)": CUSTOMER_TAG,
            "Login Tag (openmrs_login_location_tag)": LOGIN_TAG,
            "Visit Tag (openmrs_visit_location_tag)": VISIT_TAG,
            "OHC ID Attribute (openmrs_ohc_id_attribute_uuid)": OHC_ID_ATTRIBUTE,
            "Customer Code Attribute (openmrs_customer_code_attribute_uuid)": CUSTOMER_CODE_ATTRIBUTE,
            "Bharath Clinic Location UUID (openmrs_bharath_clinic_location_uuid)": BHARATH_CLINIC_UUID,
        }

        for label, value in required.items():
            if not value:
                raise UserError(
                    _("%s System Parameter is not configured.") % label
                )

        try:
            # -----------------------------------------------------
            # 1. PARENT (CUSTOMER) LOCATION
            #    a) stored UUID, but only if it really exists in
            #       OpenMRS and is this customer's location
            #    b) else exact-name lookup
            #    c) else create it
            # -----------------------------------------------------
            parent_uuid = False

            stored_uuid = customer.parent_location_uuid
            if stored_uuid:
                stored_loc = self._openmrs_get_location(
                    base_url, stored_uuid, auth, headers
                )
                if (
                    stored_loc
                    and not stored_loc.get("retired")
                    and (stored_loc.get("name") or "").strip().lower()
                    == (customer.name or "").strip().lower()
                ):
                    parent_uuid = stored_uuid
                else:
                    _logger.warning(
                        "Stored parent location %s for customer %s is not "
                        "valid in OpenMRS, looking it up again.",
                        stored_uuid, customer.name,
                    )

            if not parent_uuid:
                parent_uuid = self._openmrs_find_location(
                    base_url, customer.name, auth, headers
                )

            if parent_uuid:
                _logger.info("Parent Location exists : %s", parent_uuid)
            else:
                parent_uuid = self._openmrs_post_location(
                    base_url,
                    {
                        "name": customer.name,
                        "description": customer.name,
                        "tags": [FACILITY_TAG, CUSTOMER_TAG],
                        "parentLocation": BHARATH_CLINIC_UUID,
                    },
                    auth,
                    headers,
                    label="customer location",
                )
                _logger.info("Parent Location Created : %s", parent_uuid)

            if customer.parent_location_uuid != parent_uuid:
                customer.write({"parent_location_uuid": parent_uuid})

            # -----------------------------------------------------
            # 2. OHC LOCATION
            #    OpenMRS location names are unique, so look the OHC
            #    up by name first:
            #      - found     -> reuse it and make sure it sits
            #                     under the customer location
            #      - not found -> create it under the customer
            # -----------------------------------------------------
            location_uuid = self._openmrs_find_location(
                base_url, self.name, auth, headers
            )

            if location_uuid:
                _logger.info("OHC Location already exists : %s", location_uuid)
                self._openmrs_ensure_parent(
                    base_url, location_uuid, parent_uuid, auth, headers
                )
            else:
                attributes = []
                if self.ohc_id:
                    attributes.append({
                        "attributeType": OHC_ID_ATTRIBUTE,
                        "value": str(self.ohc_id),
                    })
                if customer.customer_code:
                    attributes.append({
                        "attributeType": CUSTOMER_CODE_ATTRIBUTE,
                        "value": str(customer.customer_code),
                    })

                location_uuid = self._openmrs_post_location(
                    base_url,
                    {
                        "name": self.name,
                        "description": self.name,
                        "tags": [LOGIN_TAG, VISIT_TAG],
                        "parentLocation": parent_uuid,
                        "attributes": attributes,
                    },
                    auth,
                    headers,
                    label="OHC location",
                )
                _logger.info("OHC Location Created : %s", location_uuid)

                # Verify the parent really got saved, fix it if not
                self._openmrs_ensure_parent(
                    base_url, location_uuid, parent_uuid, auth, headers
                )

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status in (401, 403):
                raise UserError(_(
                    "OpenMRS rejected the login (HTTP %s).\n\n"
                    "Check OPENMRS_USERNAME / OPENMRS_PASSWORD in the Odoo "
                    "environment and that the user has permission to manage "
                    "locations."
                ) % status)
            raise UserError(_(
                "OpenMRS returned an error.\n\nStatus Code : %s\n\n%s"
            ) % (status, e.response.text[:500] if e.response is not None else str(e)))

        except requests.exceptions.RequestException as e:
            raise UserError(_(
                "Unable to connect to the Clinical server.\n\n%s"
            ) % str(e))

        self.write({"location_uuid": location_uuid})

    def sync_openmrs_location(self):
        """
        Synchronize OHC with OpenMRS.
        """
        self.ensure_one()

        if self.location_uuid:
            _logger.info("OpenMRS location already synced.")
            return

        self.create_openmrs_location()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    parent_location_uuid = fields.Char(
        string="Parent Location UUID"
    )
