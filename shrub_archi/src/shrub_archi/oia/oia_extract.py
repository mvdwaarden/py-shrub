import json
from typing import List

from shrub_archi.oia.model.oia_model import OiaLocalView, Authorizations, Identity
from shrub_archi.oia.oia_api import OiaApiObjectFactory, OiaApi
from shrub_archi.oia.oia_test_data import TEST_AUTHORIZATIONS


def oia_get_users(api: OiaApi, local_view: OiaLocalView) -> List[Identity]:
    json_dict = api.get_identities()
    factory = OiaApiObjectFactory(local_view=local_view)
    users = factory.create_identities(json_dict)

    return users


def oia_extract_authorizations(environment: str, oia_api: str,
                               local_view: OiaLocalView = None) -> OiaLocalView:
    if not local_view:
        local_view = OiaLocalView()
    api = OiaApi(application=environment, base_url=oia_api)

    oia_get_users(api, local_view)

    return local_view


def test_extract():
    local_view = OiaLocalView()
    users = OiaApiObjectFactory(local_view).create_identities(json.loads(TEST_AUTHORIZATIONS))
    print(users)

    dict_local = local_view.to_dict()
    with open("oia_local_view.json", "w") as ofp:
        ofp.write(json.dumps(dict_local))
    local_view_read_back = OiaLocalView()
    with open("oia_local_view.json", "r") as ipf:
        local_view_read_back.from_dict(json.loads(ipf.read()))
    with open("oia_local_view_read_back.json", "w") as ofp:
        ofp.write(json.dumps(local_view_read_back.to_dict()))

    oia_cln = OiaApi(base_url="dont_care", application="whatever")

    oia_cln.update_identity(list(local_view.map_identities.values())[0],
                            Authorizations(local_view.map_authorizations.values()))