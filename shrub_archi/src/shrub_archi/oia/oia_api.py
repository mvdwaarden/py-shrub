import json

import requests

from shrub_archi.connectors.oracle.token import oracle_get_token
from shrub_archi.oia.model.oia_model import OiaLocalView, Identity, Role, Resource, ResourceType, Authorization
from shrub_util.api.token import Token
from .oia_test_data import TEST_AUTHORIZATIONS


class OiaApiObjectFactory:
    def __init__(self, local_view):
        self.local_view: OiaLocalView = local_view

    def create_users(self, json_dict: dict):
        result = []
        if "items" not in json_dict:
            return result
        for item in json_dict["items"]:
            u = Identity()
            u.name = item["userName"]
            u.email = item["email"]
            u.full_name = item["fullName"]
            u.status = item["status"]
            u.hub_admin = item["hubAdmin"]
            u.user_type = item["userType"]
            resolved_identity = self.local_view.resolve_identities(u)
            if "workspaces" in item:
                for json_workspace in item["workspaces"]:
                    w = Resource()
                    w.type = ResourceType.WORKSPACE
                    w.name = json_workspace["name"]
                    resolved_resource = self.local_view.resolve_resource(w)
                    if "roles" in json_workspace:
                        json_roles = json_workspace["roles"]
                        for json_role in json_roles:
                            r = Role()
                            r.name = json_role
                            resolved_role = self.local_view.resolve_role(r)
                            a = Authorization()
                            a.identity = resolved_identity
                            a.resource = resolved_resource
                            a.role = resolved_role
                            resolved_authorization = self.local_view.resolve_authorization(a)
            result.append(resolved_identity)
        return result


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
        if False:
            response = requests.request("GET", self._get_url(self.USERS_URI), headers=self._get_headers(), data="")

            print(response.text)

        test_extract()


def test_extract():
    local_view = OiaLocalView()
    users = OiaApiObjectFactory(local_view).create_users(json.loads(TEST_AUTHORIZATIONS))
    print(users)


    dict_local = local_view.to_dict()
    with open("oia_local_view.json", "w") as ofp:
        ofp.write(json.dumps(dict_local))
    local_view_read_back = OiaLocalView()
    with open("oia_local_view.json", "r") as ipf:
        local_view_read_back.from_dict(json.loads(ipf.read()))
    with open("oia_local_view_read_back.json", "w") as ofp:
        ofp.write(json.dumps(local_view_read_back.to_dict()))