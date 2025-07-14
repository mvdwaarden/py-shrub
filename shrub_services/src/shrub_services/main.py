import shrub_util.core.logging as logging
from shrub_util.core.arguments import Arguments
from shrub_util.qotd.qotd import QuoteOfTheDay
from shrub_util.core.config import Config
from shrub_services.music.get_token import apple_get_dev_token
from shrub_services.music.playlist import SpotifyApi, Synchronizer, AppleMusicApi, MusicLocalViewReaderApi
from shrub_services.music.model.music_model import MusicLocalView
from shrub_services.music.writers.json_writer import music_write_json
from shrub_services.music.readers.json_reader import music_read_json
from enum import Enum
import datetime

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
    OPP_SYNCHRONIZE_PROFILE = "profile"
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
        if True or SynchronizeFunction.OPP_SYNCHRONIZE_PLAYLISTS.value == func_synchronize:
            profile = args.get_arg("profile")
            dry_run = args.has_arg("dry-run")
            client_id = args.get_arg("client-id")
            client_secret = args.get_arg("client-secret")
            path = args.get_arg("path")
            redirect_uri = args.get_arg("redirect-uri", "http://localhost:8888/callback/")
            dev_token_file = args.get_arg("dev-token")
            user_token_file = args.get_arg("user-token")
            from_provider = args.get_arg("from")
            to_provider = args.get_arg("to")
            with open(dev_token_file, "r") as ifp:
                dev_token = ifp.read()
            with open(user_token_file, "r") as ifp:
                user_token = ifp.read()
            apple_provider = AppleMusicApi(dev_token=dev_token, user_token=user_token)
            spotify_provider = SpotifyApi(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
            local_view_provider = MusicLocalView()
            if profile:
                music_read_json(local_view_provider, profile)
                src_service = local_view_provider
            elif from_provider == "spotify":
                src_service = spotify_provider
            else:
                src_service = apple_provider
            if to_provider == "apple":
                target_service = apple_provider
            else:
                target_service = spotify_provider

            logging.getLogger().info(f"synchronize from {src_service.__class__.__name__} to {target_service.__class__.__name__}")

            syncher = Synchronizer(source=src_service, target=target_service, dry_run=True)
            syncher.synchronize_profile()
            music_write_json(src_service.local_view, f"music_profile_{datetime.datetime.now().strftime("%Y%m%d-%H:%M:%S")}")
    else:
        pass
