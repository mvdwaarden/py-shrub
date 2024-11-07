from typing import List

import requests

from shrub_archi.connectors.oracle.token import oracle_oia_get_token
from shrub_archi.iam.model.iam_model import Role, ResourceType, Resource, Authorization, Authorizations
from shrub_archi.oia.model.oia_model import Identity, OiaLocalView
from shrub_util.api.token import Token
from shrub_util.generation.template_renderer import TemplateRenderer, get_dictionary_loader


class OiaApiObjectFactory:
    def __init__(self, local_view):
        self.local_view: OiaLocalView = local_view

    def create_identities(self, json_dict: dict) -> List[Identity]:
        result: List[Identity] = []
        if "items" not in json_dict:
            return result
        for item in json_dict["items"]:
            u = Identity()
            u.name = item["userName"]
            if "email" in item:
                u.email = item["email"]
            if "fullName" in item:
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
            self.token = oracle_oia_get_token(self.application)

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

    def get_identities(self) -> List[Identity]:
        response = requests.request("GET", self._get_url(self.USERS_URI), headers=self._get_headers(), data="")

        return response.json()

    def update_identity(self, identity: Identity, authorizations: Authorizations):
        request_template = """{
                "userName": "{{ identity.email.lower() }}",
                "email": "{{ identity.email }}",
                "fullName": "{{ identity.full_name }}",
                "hubAdmin": {{ 'true' if identity.hub_admin else 'false'}},
                "workspaces": [
                    {% for workspace in authorizations.get_resources_for_identity(identity) %}
                    {
                        "name": "{{ workspace.name }}",
                        "roles": [
                        {% for role in authorizations.get_roles_for_identity_resource(identity, workspace) %}                        
                            "{{ role.name }}" {% if not loop.last  %},{% endif %}
                        {% endfor %}
                        ]
                    }{% if not loop.last  %},{% endif %}
                    {% endfor %}  
                ]                  
            }"""
        tr = TemplateRenderer({"request": request_template}, get_loader=get_dictionary_loader)
        request = tr.render("request", identity=identity, authorizations=authorizations)
        response = requests.request("PATCH", self._get_url(self.USERS_URI), headers=self._get_headers(), data=request)
        print(f"update  {identity.email} : {response.status_code}")

    def delete_identity(self, identity: Identity):
        response = requests.request("DELETE", f"{self._get_url(self.USERS_URI)}/{identity.email.lower()}",
                                    headers=self._get_headers())
        print(f"delete {identity.email} : {response.status_code}")

    def activate_identity(self, identity: Identity):
        request = f"""{{
                       "userName": "{ identity.email.lower() }",
                       "status": "{ identity.status }"                                       
                   }}"""
        response = requests.request("PATCH", f"{self._get_url(self.USERS_URI)}/{identity.email.lower()}",
                                    headers=self._get_headers(), data=request)
        print(f"set status of  {identity.email} to {identity.status}: {response.status_code}")


def oia_get_users(api: OiaApi, local_view: OiaLocalView) -> List[Identity]:
    json_dict = api.get_identities()
    factory = OiaApiObjectFactory(local_view=local_view)
    users = factory.create_identities(json_dict)

    return users
