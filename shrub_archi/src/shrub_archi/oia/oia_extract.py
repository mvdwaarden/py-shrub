import json

from shrub_archi.oia.model.oia_model import OiaLocalView
from shrub_archi.iam.model.iam_model import Authorizations
from shrub_archi.oia.oia_api import OiaApiObjectFactory, OiaApi, oia_get_users
from shrub_archi.oia.oia_test_data import TEST_AUTHORIZATIONS


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
