import json

import shrub_util.core.logging as logging
from shrub_archi.connectors.azure.token import azure_get_token
from .cmdb_api import CmdbApiObjectFactory, CmdbApi
from .cmdb_test_data import RETRIEVE_CI_RELATION_SHIPS_RESPONSE, RETRIEVE_CI_BY_AUTHORIZATION_RESPONSE, \
    RETRIEVE_CI_INFO_BY_KEY_RESPONSE
from .model.cmdb_model import CmdbLocalView, ConfigurationItem, ConfigurationItemRelation
from shrub_util.core.iteration_helpers import list_block_iterator


def cmdb_extract(environment: str, emails: list, cmdb_api: str, source: str, extra_cis: list = None,
                 local_view: CmdbLocalView = None, test_only: bool =False) -> CmdbLocalView:

    token = azure_get_token(environment)
    api = CmdbApi(base_uri=cmdb_api, token=token,
                  source=source)

    if local_view:
        result = local_view
    else:
        result = CmdbLocalView()
    factory = CmdbApiObjectFactory(local_view=result)
    cis = cmdb_get_configuration_items_by_authorization(api, factory, emails)

    if extra_cis:
        for ci in [ci for ci in extra_cis if ci not in cis]:
            cis.append(ci)
    recursion_count = 0
    max_block_size = 100
    max_recursion_count = 3
    map_ci_retrieval_cache = {}
    while len(cis) > 0 and recursion_count < max_recursion_count:
        for cis_block in list_block_iterator(cis, max_block_size):
            resolved_cis = cmdb_get_info_for_configuration_item_by_key(api, factory, cis_block)
            for ci in resolved_cis:
                map_ci_retrieval_cache[ci.key] = ci
        cis = []
        for resolved_ci in resolved_cis:
            relations = cmdb_get_relation_ships_by_configuration_item(api, factory, resolved_ci)
            for relation in relations:
                if relation.src.key not in map_ci_retrieval_cache and relation.src.key not in cis:
                    cis.append(relation.src.key)
                if relation.dst.key not in map_ci_retrieval_cache and relation.dst.key not in cis:
                    cis.append(relation.dst.key)
        recursion_count += 1

    return result


def cmdb_get_configuration_items_by_authorization(api: CmdbApi, factory: CmdbApiObjectFactory, emails: str) -> []:
    response_json = api.get_configuration_items_by_authorization(emails)
    cis = factory.get_configuration_item_ids_from_retreive_ci_by_authorization_result(response_json)

    return cis


def cmdb_get_info_for_configuration_item_by_key(api: CmdbApi, factory: CmdbApiObjectFactory, keys: list) -> ConfigurationItem:
    response_json = api.get_configuration_item_info_by_key(keys)
    cis = factory.create_configuration_item_from_retrieve_ci_info_result_json(response_json)

    return cis


def cmdb_get_relation_ships_by_configuration_item(api: CmdbApi, factory: CmdbApiObjectFactory, ci: ConfigurationItem) -> list:
    response_json = api.get_relation_ships_by_configuration_item_name(ci.name)
    downstream = upstream = False
    relations = []
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
            relations.append(factory.local_view.resolve_relation(relation))
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
            relations.append(factory.local_view.resolve_relation(relation))

    if not upstream and not downstream:
        logging.get_logger().warning(f"no upstream and downstream for {ci}")

    return relations


def test_cmdb_extract_factory() -> CmdbLocalView:
    local_view = CmdbLocalView()
    result = json.loads(RETRIEVE_CI_RELATION_SHIPS_RESPONSE)
    factory = CmdbApiObjectFactory(local_view=local_view)
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
