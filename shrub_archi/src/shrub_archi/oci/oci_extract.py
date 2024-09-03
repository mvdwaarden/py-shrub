from shrub_archi.oci.model.oci_model import OciLocalView
from shrub_archi.oci.oci_api import OciApi, OciApiObjectFactory
from shrub_archi.oci.oci_test_data import TEST_USERS_DATA
import json


def oci_extract_users(environment: str, base_url: str) -> OciLocalView:
    local_view = OciLocalView()
    factory = OciApiObjectFactory(local_view=local_view)
    api = OciApi(environment=environment, base_url=base_url)
    json_dict = api.get_identities()
    factory.create_identities(json_dict)

    return local_view


def test_extract():
    local_view = OciLocalView()
    users = OciApiObjectFactory(local_view).create_identities(json.loads(TEST_USERS_DATA))
    print(users)

    dict_local = local_view.to_dict()
    with open("oci_local_view.json", "w") as ofp:
        ofp.write(json.dumps(dict_local))
    local_view_read_back = OciLocalView()
    with open("oci_local_view.json", "r") as ipf:
        local_view_read_back.from_dict(json.loads(ipf.read()))
    with open("oci_local_view_read_back.json", "w") as ofp:
        ofp.write(json.dumps(local_view_read_back.to_dict()))

