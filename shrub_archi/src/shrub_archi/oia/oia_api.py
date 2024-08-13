from ..connectors.oracle.token import oracle_get_token
from shrub_util.api.token import Token
import requests


class OiaApi:
    USERS_URI = "users"

    def __init__(self, application: str, base_url: str, version: str = None):
        self.application: str = application
        self.base_url: str = base_url
        self.version: str = version
        self.token: Token = None

    def _get_token(self):
        if not self.token or self.token.expires_in_actual() < 30:
            self.token = oracle_get_token(self.application)

        return self.token

    def _get_url(self, function: str):
        if self.version:
            url = f"{self.base_url}/{self.version}/{function}"
        else:
            url = f"{self.base_url}/{function}"
        return url

    def _get_headers(self):
        headers = {
            'Content-Type': 'application/json',
            "Authorization": f"Bearer {self._get_token().access_token}"
        }
        return headers

    def get_users(self):
        response = requests.request("GET", self._get_url(self.USERS_URI), headers=self._get_headers(), data="")

        print(response.text)


