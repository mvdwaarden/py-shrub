import shrub_util.core.logging as logging
from shrub_util.core.arguments import Arguments
from shrub_util.qotd.qotd import QuoteOfTheDay
from shrub_util.core.config import Config
from shrub_services.music.get_token import apple_get_dev_token
from shrub_services.music.playlist import SpotifyApi, Synchronizer, AppleMusicApi
from enum import Enum

usage = """
    Shrubbery Subscription Services Tools, assumes:
    - Either
      - SHRUB_CONFIG_INI environment variable is set and points to config.ini
      - config-ini argument is passed and points to config.ini
    - The directory location of the config.ini is config_path,
      and can be referred to in the configuration as {config_path}
    - The config.ini contains the connections definitions. Connection sections
      have the name [ExternalApi-<connection name>]

    Mode - <mode>
    <description>
    Parameters:
    - <param1>: <description>
"""

class KeyFunction(Enum):
    OPP_APPLE_DEV_TOKEN = "apple_dev_token"
    OPP_SPOTIFY_DEV_TOKEN = "spotify_token"
    @staticmethod
    def is_operation(operation: str):
        return operation and operation in [e.value for e in KeyFunction]

class SynchronizeFunction(Enum):
    OPP_SYNCHRONIZE_PLAYLISTS = "playlists"
    @staticmethod
    def is_operation(operation: str):
        return operation and operation in [e.value for e in SynchronizeFunction]

logging.configure_console()
Config.ENV_CONFIG_INI =  "SHRUB_CONFIG_INI"
if __name__ == "__main__":

    def do_print_usage():
        qotd = QuoteOfTheDay().get_quote()
        print(usage + f"\n    {qotd['quote']} - {qotd['source']}")

    args = Arguments()
    func_help = args.has_arg("help")
    func_get_key = args.get_arg("get-key")
    func_synchronize = args.get_arg("synch")

    if func_help:
        do_print_usage()
    elif KeyFunction.is_operation(func_get_key):
        key = args.get_arg("key")
        team = args.get_arg("team")
        path = args.get_arg("path")
        if KeyFunction.OPP_APPLE_DEV_TOKEN.value == func_get_key:
            apple_get_dev_token(team, key, path)
    elif SynchronizeFunction.is_operation(func_synchronize):
        if SynchronizeFunction.OPP_SYNCHRONIZE_PLAYLISTS.value == func_synchronize:
            client_id = args.get_arg("client_id")
            client_secret = args.get_arg("client_secret")
            path = args.get_arg("path")
            redirect_uri = args.get_arg("redirect_uri")
            s_cln = SpotifyApi(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
            playlists = s_cln.get_playlists()
            # for playlist in playlists:
            #     s_cln.get_playlist(playlist)
            #t_cln = AppleMusicApi()
            syncher = Synchronizer(src=s_cln, dst=s_cln)
            syncher.sychronize()
    else:
        pass