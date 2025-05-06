import re
from typing import List

import requests

from shrub_archi.cmdb.model.cmdb_model import CmdbLocalView, ConfigurationItem, ConfigAdmin, Manager, Department, \
    Vendor, ServiceComponent
from shrub_util.api.token import Token
from shrub_util.core import logging as logging


class CmdbApiObjectFactory:
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
        resolved_ci.system_owner = resolved_man
        dep = Department()
        dep.name = source_dict[f"{prefix}Department"]
        resolved_dep = self.local_view.resolve_department(dep)
        resolved_ci.department = resolved_dep
        return resolved_ci

    def create_configuration_item_from_retrieve_ci_info_result_json(self, json_dict: dict) -> List[ConfigurationItem]:
        resolved_cis = []

        if not json_dict or "information" not in json_dict or len(json_dict["information"]) <= 0:
            return []
        for source_dict in json_dict["information"]:
            try:
                ci = ConfigurationItem()
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
                if "SystemOwner" in source_dict:
                    man = Manager()
                    # custom key = email!
                    man.email = source_dict["SystemOwner"]
                    resolved_man = self.local_view.resolve_manager(man)
                    resolved_ci.system_owner = resolved_man

                if "SystemOwnerDepartment" in source_dict:
                    dep = Department()
                    # custom key = email!
                    dep.name = source_dict["SystemOwnerDepartment"]
                    resolved_dep = self.local_view.resolve_department(dep)
                    resolved_ci.department = resolved_dep

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
                resolved_cis.append(resolved_ci)
            except Exception as ex:
                logging.get_logger().error(f"issue creating ConfigurationInfo from {json_dict}")

        return resolved_cis

    def get_configuration_item_ids_from_retreive_ci_by_authorization_result(self, json_dict: dict):
        result = []
        if not json_dict or "information" not in json_dict or len(json_dict["information"]) <= 0:
            return result
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
    RETRIEVE_CI_AUTHORIZATION_URI = "retrieveCIAuthorization"

    def __init__(self, source: str, base_uri: str, token: Token):
        self.source = source
        self.base_uri = base_uri
        self.token = token

    def _call_retrieve_api(self, function, request_builder) -> dict:
        logging.get_logger().info(f"start calling {function}")
        request = request_builder()
        response = requests.post(
            url=self._get_url(function),
            headers=self._get_headers(),
            data=request)
        if response.ok:
            result = response.json()[function]
            logging.get_logger().info(f"done calling {function} : OK")
        else:
            result = None
            logging.get_logger().info(f"done calling {function} for source {self.source}: NOK {response.status_code}")
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

    def get_configuration_item_info_by_key(self, keys: list):
        def get_retrieve_ci_info_request():
            return f"""{{
                          "{self.RETRIEVE_CI_INFO_BY_KEY_URI}": {{
                            "Key": [
                               "{'","'.join(keys)}"
                            ],
                            "RequestType": "CI",
                            "Source": "{self.source}"
                          }}
                        }}"""

        return self._call_retrieve_api(self.RETRIEVE_CI_INFO_BY_KEY_URI, get_retrieve_ci_info_request)

    def get_configuration_items_by_authorization(self, emails: list):
        def get_retrieve_ci_by_authorization_request():
            return f"""{{
                            "{self.RETRIEVE_CI_AUTHORIZATION_URI}": {{
                                "Key": [
                                    "{'","'.join(emails)}"
                                ],
                                "Type": "user",
                                "Source": "{self.source}"
                            }}
                        }}"""

        return self._call_retrieve_api(self.RETRIEVE_CI_AUTHORIZATION_URI, get_retrieve_ci_by_authorization_request)

    def _get_url(self, uri: str) -> str:
        return f"{self.base_uri}{uri}"

    def _get_headers(self) -> dict:
        return {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.token.access_token}"
        }
