import json
import re

import requests

import shrub_util.core.logging as logging
from shrub_archi.connectors.azure.token import azure_get_token
from shrub_util.api.token import Token
from .cmdb_test_data import RETRIEVE_CI_RELATION_SHIPS_RESPONSE, RETRIEVE_CI_BY_AUTHORIZATION_RESPONSE, \
    RETRIEVE_CI_INFO_BY_KEY_RESPONSE
from .model.cmdb_model import CmdbLocalView, ConfigurationItem, ConfigAdmin, Manager, Department, Vendor, \
    ServiceComponent, ConfigurationItemRelation


class CmdbApiFactory:
    def __init__(self, local_view: CmdbLocalView):
        self.local_view = local_view

    def create_configuration_item_from_retrieve_relation_ship_result_json(self, json_dict: dict,
                                                                          prefix: str = "") -> ConfigurationItem:
        ci = ConfigurationItem()
        source_dict = json_dict
        ci.name = source_dict[f"{prefix}CIName"]
        resolved_ci = self.local_view.resolve_configuration_item(ci)
        resolved_ci.key = source_dict[f"{prefix}CIID"]
        resolved_ci.status = source_dict[f"{prefix}CIStatus"]
        resolved_ci.sub_type = source_dict[f"{prefix}CISubtype"]
        resolved_ci.type = source_dict[f"{prefix}CIType"]
        ca = ConfigAdmin()
        ca.name = source_dict[f"{prefix}ConfigAdmin"]
        resolved_ca = self.local_view.resolve_config_admin(ca)
        resolved_ca.functional_email = source_dict[f"{prefix}FunctionalEmail"]
        resolved_ci.config_admin = resolved_ca
        man = Manager()
        # custom key = email!
        man.email = source_dict[f"{prefix}ManagerEmail"]
        resolved_man = self.local_view.resolve_manager(man)
        resolved_man.name = source_dict[f"{prefix}ManagerName"]
        resolved_ci.manager = resolved_man
        dep = Department()
        dep.name = source_dict[f"{prefix}Department"]
        resolved_dep = self.local_view.resolve_department(dep)
        resolved_ci.department = resolved_dep
        return resolved_ci

    def create_configuration_item_from_retrieve_ci_info_result_json(self, json_dict: dict) -> ConfigurationItem:
        ci = ConfigurationItem()
        source_dict = json_dict["information"][0]
        ci.name = source_dict["CiName"]
        resolved_ci = self.local_view.resolve_configuration_item(ci)
        if "AicClassification" in source_dict:
            resolved_ci.aic = source_dict["AicClassification"]
        resolved_ci.key = source_dict["CiID"]
        resolved_ci.status = source_dict["Status"]
        resolved_ci.sub_type = source_dict["CiSubtype"]
        resolved_ci.type = source_dict[("CiType")]
        if "Description" in source_dict:
            if source_dict["Description"]:
                resolved_ci.description = ""
                for line in source_dict["Description"]:
                    if line:
                        resolved_ci.description += line
        if "Title" in source_dict:
            resolved_ci.title = source_dict["Title"]
        if "Environment" in source_dict:
            resolved_ci.environments = []
            for env in source_dict["Environment"]:
                resolved_ci.environments.append(env)
        if "IAMProvisioningMethod" in source_dict:
            resolved_ci.iam_provisioning_methods = []
            for prov in source_dict["IAMProvisioningMethod"]:
                resolved_ci.iam_provisioning_methods.append(prov)

        ca = ConfigAdmin()
        ca.name = source_dict["ConfigAdminGroup"]
        resolved_ca = self.local_view.resolve_config_admin(ca)
        resolved_ci.config_admin = resolved_ca
        if "BusinessOwner" in source_dict:
            man = Manager()
            # custom key = email!
            man.email = source_dict["BusinessOwner"]
            resolved_man = self.local_view.resolve_manager(man)
            resolved_ci.business_owner = resolved_man

        if "Vendor" in source_dict:
            vendor = Vendor()
            vendor.name = source_dict["Vendor"]
            resolved_vendor = self.local_view.resolve_vendor(vendor)
            resolved_ci.vendor = resolved_vendor

        if "RelatedServiceComponent" in source_dict:
            sc = ServiceComponent()
            sc.name = source_dict["RelatedServiceComponent"]
            resolved_sc = self.local_view.resolve_service_component(sc)
            resolved_ci.related_service_component = resolved_sc

        return resolved_ci

    def get_configuration_item_ids_from_retreive_ci_by_authorization_result(self, json_dict: dict):
        result = []
        source_dict = json_dict["information"][0]["CIName"]
        matcher = re.compile("(.*) \\((.*)\\)")
        for ci_name in source_dict:
            match = matcher.match(ci_name)
            if match:
                name = match.group(1)
                id = match.group(2)
                result.append(id)
        return result


class CmdbApi:
    RETRIEVE_RELATION_SHIPS_BY_NAME_URI = "retrieveCIRelationshipInfoByKey"
    RETRIEVE_CI_INFO_BY_KEY_URI = "retrieveCiInfoByKey"
    RETRIEVE_CI_AUTHORIZATION = "retrieveCIAuthorization"

    def __init__(self, source: str, base_uri: str, token: Token):
        self.source = source
        self.base_uri = base_uri
        self.token = token

    def _call_retrieve_api(self, function, request_builder) -> dict:
        response = requests.post(
            url=self._get_url(function),
            headers=self._get_headers(),
            data=request_builder())
        if response.ok:
            result = response.json()[function]
        else:
            result = None
        return result

    def get_relation_ships_by_configuration_item_name(self, name: str):
        def get_retrieve_relation_ships_request():
            return f"""{{
                          "{self.RETRIEVE_RELATION_SHIPS_BY_NAME_URI}": {{
                            "Key": "{name}",
                            "Source": "{self.source}"
                          }}
                        }}"""

        return self._call_retrieve_api(self.RETRIEVE_RELATION_SHIPS_BY_NAME_URI, get_retrieve_relation_ships_request)

    def get_configuration_item_info_by_key(self, key: str):
        def get_retrieve_ci_info_request():
            return f"""{{
                          "{self.RETRIEVE_CI_INFO_BY_KEY_URI}": {{
                            "Key": [
                              "{key}"
                            ],
                            "RequestType": "CI",
                            "Source": "{self.source}"
                          }}
                        }}"""

        return self._call_retrieve_api(self.RETRIEVE_CI_INFO_BY_KEY_URI, get_retrieve_ci_info_request)

    def get_configuration_items_by_authorization(self, email: str):
        def get_retrieve_ci_by_authorization():
            return f"""{{
                            "{self.RETRIEVE_CI_AUTHORIZATION}": {{
                                "Key": [
                                    "{email}"
                                ],
                                "Type": "user",
                                "Source": "{self.source}"
                            }}
                        }}"""

        return self._call_retrieve_api(self.RETRIEVE_CI_AUTHORIZATION, get_retrieve_ci_by_authorization)

    def _get_url(self, uri: str) -> str:
        return f"{self.base_uri}{uri}"

    def _get_headers(self) -> dict:
        return {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.token.access_token}"
        }


def cmdb_extract(environment: str, email: str, cmdb_api: str, source: str,
                 local_view: CmdbLocalView = None, test_only: bool =False) -> CmdbLocalView:

    local_view = test_cmdb_extract_factory()
    if test_only:
        return local_view
    else:
        local_view = None

    token = azure_get_token(environment)
    api = CmdbApi(base_uri=cmdb_api, token=token,
                  source=source)

    if local_view:
        result = local_view
    else:
        result = CmdbLocalView()
    factory = CmdbApiFactory(local_view=result)

    for key in cmdb_get_configuration_items_by_authorization(api, factory, email):
        ci = cmdb_get_info_for_configuration_item_by_key(api, factory, key)
        cmdb_get_relation_ships_by_configuration_item(api, factory, ci)

    return result


def cmdb_get_configuration_items_by_authorization(api: CmdbApi, factory: CmdbApiFactory, email: str) -> []:
    response_json = api.get_configuration_items_by_authorization(email)
    cis = factory.get_configuration_item_ids_from_retreive_ci_by_authorization_result(response_json)

    return cis


def cmdb_get_info_for_configuration_item_by_key(api: CmdbApi, factory: CmdbApiFactory, key: str) -> ConfigurationItem:
    response_json = api.get_configuration_item_info_by_key(key)
    ci = factory.create_configuration_item_from_retrieve_ci_info_result_json(response_json)

    return ci


def cmdb_get_relation_ships_by_configuration_item(api: CmdbApi, factory: CmdbApiFactory, ci: ConfigurationItem):
    response_json = api.get_relation_ships_by_configuration_item_name(ci.name)
    downstream = upstream = False
    if "downstreamCIs" in response_json:
        for downstream_ci_json in response_json["downstreamCIs"]:
            downstream_ci = factory.create_configuration_item_from_retrieve_relation_ship_result_json(
                json_dict=downstream_ci_json,
                prefix="Downstream")
            print(f"downstream: {ci}")
            downstream = True
            relation = ConfigurationItemRelation()
            relation.src = ci
            relation.dst = downstream_ci
            relation.type = downstream_ci_json["DownstreamRelationshipSubtype"]
            factory.local_view.resolve_relation(relation)
    if "upstreamCIs" in response_json:
        for upstream_ci_json in response_json["upstreamCIs"]:
            upstream_ci = factory.create_configuration_item_from_retrieve_relation_ship_result_json(
                json_dict=upstream_ci_json,
                prefix="Upstream")
            print(f"upstream: {ci}")
            upstream = True
            relation = ConfigurationItemRelation()
            relation.src = upstream_ci
            relation.dst = ci
            relation.type = upstream_ci_json["UpstreamRelationshipSubtype"]
            factory.local_view.resolve_relation(relation)

    if not upstream and not downstream:
        logging.get_logger().warning(f"no upstream and downstream for {ci}")


def test_cmdb_extract_factory() -> CmdbLocalView:
    local_view = CmdbLocalView()
    result = json.loads(RETRIEVE_CI_RELATION_SHIPS_RESPONSE)
    factory = CmdbApiFactory(local_view=local_view)
    for down_stream_ci in result["downstreamCIs"]:
        ci = factory.create_configuration_item_from_retrieve_relation_ship_result_json(json_dict=down_stream_ci,
                                                                                       prefix="Downstream")
        print(f"downstream: {ci}")

    for up_stream_ci in result["upstreamCIs"]:
        ci = factory.create_configuration_item_from_retrieve_relation_ship_result_json(json_dict=up_stream_ci,
                                                                                       prefix="Upstream")
        print(f"upstream: {ci}")

    result = json.loads(RETRIEVE_CI_INFO_BY_KEY_RESPONSE)
    ci = factory.create_configuration_item_from_retrieve_ci_info_result_json(json_dict=result)
    print(f"info: {ci}")
    result = json.loads(RETRIEVE_CI_BY_AUTHORIZATION_RESPONSE)
    cis = factory.get_configuration_item_ids_from_retreive_ci_by_authorization_result(json_dict=result)
    print(f"configuration items: {cis}")
    local_view_dict = local_view.to_dict()
    print(local_view_dict)
    new_local_view = CmdbLocalView()
    new_local_view.from_dict(local_view_dict)
    print(new_local_view.to_dict())
    return local_view
