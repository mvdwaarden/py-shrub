import msal
from shrub_util.core.config import Config, ConfigSection
from shrub_util.core.secrets import Secrets
from msal import ConfidentialClientApplication
from shrub_util.api.token import Token


def _get_config_section(application: str) -> ConfigSection:
    return Config().get_section(f"Token-{application}")


def azure_get_confidential_application(application: str) -> ConfidentialClientApplication:
    section = _get_config_section(application)
    token_url = section.get_setting("Url")
    client_id = section.get_setting("ClientId")
    secret = Secrets().get_secret(section.get_secret_reference(), "ClientSecret")
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=secret,
        authority=token_url,
        verify=False
    )
    return app


def azure_get_token(application: str) -> Token:
    """ Typically the configuration consists of two parts
    1) In config.ini
    [Secrets]
    Filename={config_path}/secrets.ini

    [Token-$application]
    Provider=Azure
    Url=https://login.microsoftonline.com/$tenant_id //Tenant ID can be found when logged in in the Azure portal
    #Alternative
    #Url=https://login.microsoftonline.com/$tenant_id/oauth2/v2.0/token
    ClientId=$client_id //This is the Application Client ID as shown in Azure
    SecretReference=$secret_reference

    2) In secrets.ini (see above)
    [Token-$application-$secret_reference]
    ClientSecret=lIf8Q~-_do_fmRsK.7QuN39oLs9oABnk9U1BvdAG
    Scopes=.default
    """
    section = _get_config_section(application)
    scopes = Secrets().get_secret(section.get_secret_reference(), "Scopes").split(",")
    # Acquire a token
    result = azure_get_confidential_application(application).acquire_token_for_client(scopes=scopes)

    if "access_token" in result:
        access_token = result["access_token"]
        expires_in = result.get("expires_in")
        token = Token(access_token=access_token, expires_in=expires_in)
        print("Access token retrieved")

    else:
        token = None
        print("Error:", result.get("error"), result.get("error_description"))
    return token


def azure_remove_tokens(application: str):
    azure_get_confidential_application(application).remove_tokens_for_client()
