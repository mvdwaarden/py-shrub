import csv

import shrub_util.core.logging as logging
from shrub_util.core.arguments import Arguments
from shrub_util.qotd.qotd import QuoteOfTheDay
from shrub_util.core.config import Config
from shrub_scraper.events.architecture_events import scrape_danw_architecture_events, scrape_knvi_architecture_events
from shrub_scraper.events.model import Event

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
    file = args.get_arg("file")
    if help:
        do_print_usage()
    else:
        with open(file, "w") as ofp:
            writer = csv.DictWriter(ofp, fieldnames=vars(Event()).keys(), delimiter=";")
            writer.writeheader()
            for fn in [scrape_danw_architecture_events, scrape_knvi_architecture_events]:
                events = fn()
                for event in events:
                    print(f"title: {event.title} @ {event.date}")
                    writer.writerow(vars(event))

