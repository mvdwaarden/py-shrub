import requests
from requests.auth import HTTPBasicAuth

from shrub_util.api.token import Token
from shrub_util.core.config import Config, ConfigSection
from shrub_util.core.secrets import Secrets


def _get_config_section(application: str) -> ConfigSection:
    return Config().get_section(f"Token-{application}")


def oracle_oia_get_token(application: str) -> Token:
    section = _get_config_section(application)
    token_url = section.get_setting("Url")
    client_id = section.get_setting("ClientId")
    secret = Secrets().get_secret(section.get_secret_reference(), "ClientSecret")
    # Acquire a token
    payload = f"grant_type=client_credentials&client_id={client_id}&client_secret={secret}"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    result = requests.request("POST", token_url, headers=headers, data=payload, verify=False)
    if result.ok:
        result_json = result.json()
        access_token = result_json["access_token"]
        expires_in = result_json.get("expires_in")
        token = Token(access_token=access_token, expires_in=expires_in)
        # TODO remove printing of token
        print("Access token retrieved")

    else:
        token = None
        print("Error:", result.get("error"), result.get("error_description"))
    return token


def oracle_oci_get_token(application: str) -> Token:
    section = _get_config_section(application)
    token_url = section.get_setting("Url")
    client_id = section.get_setting("ClientId")
    secret = Secrets().get_secret(section.get_secret_reference(), "ClientSecret")
    scopes = Secrets().get_secret(section.get_secret_reference(), "Scopes")
    # Acquire a token
    payload = f"grant_type=client_credentials&scope={scopes}"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    result = requests.request("POST", token_url, headers=headers, data=payload, auth=HTTPBasicAuth(client_id, secret),
                              verify=False)
    if result.ok:
        result_json = result.json()
        access_token = result_json["access_token"]
        expires_in = result_json.get("expires_in")
        token = Token(access_token=access_token, expires_in=expires_in)
        # TODO remove printing of token
        print("Access token:", token)

    else:
        token = None
        print("Error:", result.get("error"), result.get("error_description"))
    return token
