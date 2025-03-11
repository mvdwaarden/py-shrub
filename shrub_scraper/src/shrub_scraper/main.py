import shrub_util.core.logging as logging
from shrub_util.core.arguments import Arguments
from shrub_util.qotd.qotd import QuoteOfTheDay
from shrub_util.core.config import Config
from shrub_scraper.events.architecture_events import scrape_danw_architecture_events, scrape_knvi_architecture_events


usage = """
    Web scraper functionality, assumes:
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

logging.configure_console()
Config.ENV_CONFIG_INI =  "SHRUB_CONFIG_INI"
if __name__ == "__main__":

    def do_print_usage():
        qotd = QuoteOfTheDay().get_quote()
        print(usage + f"\n    {qotd['quote']} - {qotd['source']}")

    args = Arguments()
    help = args.has_arg("help")

    if help:
        do_print_usage()
    else:
        for fn in [scrape_danw_architecture_events, scrape_knvi_architecture_events]:
            events = fn()
            for event in events:
                # Print event details
                print(f"Title: {event.title}")
                print(f"Date: {event.date}")
                print(f"Description: {event.description}")
                print(f"URL: {event.url}")
                print('-' * 40)
            print(f"Found {len(events)}")