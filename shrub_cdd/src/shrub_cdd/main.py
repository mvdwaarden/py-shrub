import shrub_util.core.logging as logging
from shrub_util.core.arguments import Arguments
from shrub_util.qotd.qotd import QuoteOfTheDay
from shrub_cdd.readers.read_aggregated_cdd import read_aggregated_graph, aggregate_graph, write_aggregated_graph

usage = """
    Custom Shrubbery Project CDD, assumes:
    - SHRUB_CONFIG_INI environment variable is set and points to config.ini
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
if __name__ == "__main__":

    def do_print_usage():
        qotd = QuoteOfTheDay().get_quote()
        print(usage + f"\n    {qotd['quote']} - {qotd['source']}")

    args = Arguments()
    help = args.has_arg("help")
    file = args.get_arg("file")
    name = args.get_arg("name")

    if help:
        do_print_usage()
    else:
        with open(file) as ifp:
            json_str = ifp.read()

            g = read_aggregated_graph(json_str, name)

            ag = aggregate_graph(g)
        print(f"graph {g} ->  {ag}")
        write_aggregated_graph(ag, file=f"{file}.ag")
        write_aggregated_graph(g, file=f"{file}.g")

