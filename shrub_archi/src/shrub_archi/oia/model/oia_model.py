from enum import Enum
from typing import TypeVar


class Identity:
    def __init__(self):
        self.name: str = None
        self.email: str = None
        self.full_name: str = None
        self.status: str = None
        self.hub_admin: bool = None
        self.user_type: str = None

    def get_resolve_key(self):
        return self.email

    def from_dict(self, json_dict: dict) -> "Identity":
        self.name = json_dict["name"]
        self.email = json_dict["email"]
        self.full_name = json_dict["full_name"]
        self.status = json_dict["status"]
        self.hub_admin = True if json_dict["hubAdmin"] else False
        return self

    def to_dict(self) -> dict:
        the_dict = {}
        the_dict["name"] = self.name
        the_dict["email"] = self.email
        the_dict["full_name"] = self.full_name
        the_dict["status"] = self.status
        the_dict["hub_admin"] = self.hub_admin
        the_dict["user_type"] = self.user_type

        return the_dict

    def from_dict(self, the_dict: dict) -> "Identity":
        self.name = the_dict["name"]
        self.email = the_dict["email"]
        self.full_name = the_dict["full_name"]
        self.status = the_dict["status"]
        self.hub_admin = the_dict["hub_admin"]
        self.user_type = the_dict["user_type"]

        return self


class ResourceType(Enum):
    WORKSPACE = "workspace"
    UNKNOWN = "unknown"

    @staticmethod
    def from_value(value: str):
        if value == "workspace":
            return ResourceType.WORKSPACE
        else:
            return ResourceType.UNKNOWN


class Role:
    def __init__(self):
        self.name = None

    def get_resolve_key(self):
        return self.name

    def to_dict(self) -> dict:
        the_dict = {}
        the_dict["name"] = self.name

        return the_dict

    def from_dict(self, the_dict: dict) -> "Role":
        self.name = the_dict["name"]

        return self


class Resource:
    def __init__(self):
        self.name: str = None
        self.type: ResourceType = ResourceType.UNKNOWN

    def get_resolve_key(self):
        return f"{self.name}.{self.type.value}"

    def to_dict(self) -> dict:
        the_dict = {}
        the_dict["name"] = self.name
        the_dict["type"] = self.type.value

        return the_dict

    def from_dict(self, the_dict: dict) -> "Resource":
        self.name = the_dict["name"]
        self.type = ResourceType.from_value(the_dict["type"])

        return self


class Authorization:
    def __init__(self):
        self.identity: Identity = None
        self.resource: Resource = None
        self.role: Role = None

    def get_resolve_key(self):
        return f"{self.identity.get_resolve_key()}.{self.resource.get_resolve_key()}.{self.role.get_resolve_key()}"

    def to_dict(self) -> dict:
        the_dict = {}
        the_dict["identity"] = self.identity.get_resolve_key()
        the_dict["resource"] = self.resource.get_resolve_key()
        the_dict["role"] = self.role.get_resolve_key()

        return the_dict

    def from_dict(self, the_dict: dict) -> "Authorization":
        self.identity = the_dict["identity"]
        self.resource = the_dict["resource"]
        self.role = the_dict["role"]

        return self


T = TypeVar("T")


class OiaLocalView:
    def __init__(self):
        self.users = []
        self.map_identities = {}
        self.map_resources = {}
        self.map_roles = {}
        self.map_authorizations = {}

    def _resolve_object(self, map, obj: T) -> T:
        if obj.get_resolve_key() in map:
            resolved_obj = map[obj.get_resolve_key()]
        else:
            map[obj.get_resolve_key()] = obj
            resolved_obj = obj
        return resolved_obj

    def resolve_identities(self, identity: Identity) -> Identity:
        return self._resolve_object(self.map_identities, identity)

    def resolve_resource(self, resource: Resource) -> Resource:
        return self._resolve_object(self.map_resources, resource)

    def resolve_role(self, role: Role) -> Role:
        return self._resolve_object(self.map_roles, role)

    def resolve_authorization(self, auth: Authorization) -> Authorization:
        return self._resolve_object(self.map_authorizations, auth)

    def to_dict(self) -> dict:
        the_dict = {}
        the_dict["identities"] = []
        for identity in self.map_identities.values():
            the_dict["identities"].append(identity.to_dict())
        the_dict["resources"] = []
        for resource in self.map_resources.values():
            the_dict["resources"].append(resource.to_dict())
        the_dict["roles"] = []
        for role in self.map_roles.values():
            the_dict["roles"].append(role.to_dict())
        the_dict["authorizations"] = []
        for authorization in self.map_authorizations.values():
            the_dict["authorizations"].append(authorization.to_dict())
        return the_dict

    def from_dict(self, the_dict: dict) -> "Authorization":
        if "identities" in the_dict:
            for dict_identity in the_dict["identities"]:
                identity = Identity().from_dict(dict_identity)
                resolved_identity = self.resolve_identities(identity)

        if "resources" in the_dict:
            for dict_resource in the_dict["resources"]:
                resource = Resource().from_dict(dict_resource)
                resolved_resource = self.resolve_resource(resource)

        if "roles" in the_dict:
            for dict_role in the_dict["roles"]:
                role = Role().from_dict(dict_role)
                resolved_role = self.resolve_role(role)

        if "authorizations" in the_dict:
            for dict_authorization in the_dict["authorizations"]:
                authorization = Authorization().from_dict(dict_authorization)
                # resolve the keys to the objects
                authorization.identity = self.map_identities[authorization.identity]
                authorization.resource = self.map_resources[authorization.resource]
                authorization.role = self.map_roles[authorization.role]
                resolved_authorization = self.resolve_authorization(authorization)
