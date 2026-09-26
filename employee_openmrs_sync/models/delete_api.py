import logging
import requests
from requests.auth import HTTPBasicAuth

_logger = logging.getLogger(__name__)

from odoo import models, api
import requests
import logging

_logger = logging.getLogger(__name__)

class OpenMRSApi(models.AbstractModel):
    _name = 'openmrs.api'
    _description = 'OpenMRS API'

    def delete_user(self, user_uuid):
        """
        Delete OpenMRS User
        """

        if not user_uuid:
            return False

    
        
        config = self.env['ir.config_parameter'].sudo()

        base_url = config.get_param('base_url')

        # url = "%s/ws/rest/v1/user/%s" % (
        #     self.base_url(),
        #     user_uuid
        # )
        url = "%s/ws/rest/v1/user/%s" % (
            base_url.rstrip("/"),
            user_uuid
        )

        _logger.info("********Delete URL*********: %s", url)

        payload = {
            "purge": False
        }

        try:

            # response = requests.delete(
            #     url,
            #     headers=headers,
            #     json=payload,
            #     verify=False,
            #     timeout=60
            # )
            response = requests.delete(
                url,
                json=payload,
                auth=HTTPBasicAuth("superman", "Admin123"),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json;charset=UTF-8",
                },
                verify=False,
                timeout=60,
            )

            if response.status_code in [200, 204]:

                _logger.info(
                    "OpenMRS User deleted successfully : %s",
                    user_uuid
                )

                return True

            _logger.error(
                "Delete User Failed : %s",
                response.text
            )

            return False

        except Exception as e:

            _logger.exception(e)
            return False