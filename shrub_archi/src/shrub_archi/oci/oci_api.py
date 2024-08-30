import requests
from shrub_archi.connectors.oracle.token import oracle_oci_get_token
from typing import List
from shrub_archi.iam.model.iam_model import Identity
from shrub_archi.oci.model.oci_model import OciLocalView


class OciApiObjectFactory:
    def __init__(self, local_view: OciLocalView):
        self.local_view = local_view

    def create_identities(self, json_dict: dict) -> List[Identity]:
        ...


class OciApi:
    USERS_URI = "admin/v1/Users"

    def __init__(self, environment, base_url: str, version: str=None):
        self.environment = environment
        self.base_url = base_url
        self.token = None
        self.version = None

    def _get_token(self):
        if not self.token or self.token.expires_in_actual() < 30:
            self.token = oracle_oci_get_token(self.environment)

        return self.token

    def _get_url(self, function: str):
        if self.version:
            url = f"{self.base_url}/{self.version}/{function}"
        else:
            url = f"{self.base_url}/{function}"
        return url

    def get_identities(self) -> List[Identity]:
        response = requests.request("GET", self._get_url(self.USERS_URI), headers=self._get_headers(), data="")

        return response.json()

    def load_test(self):
        token = None

        token = self._get_token()

        if False:
            url = f"{self.base_url}/Users"

            payload = {}
            headers = {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
              'Authorization': '••••••'
            }

            response = requests.request("GET", url, headers=headers, data=payload)

            print(response.text)


def oci_get_users(local_view: OciLocalView, oci_api: OciApi):
    oci_api.get_identities()