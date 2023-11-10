import shrub_util.core.logging as logging
from shrub_util.core.arguments import Arguments
from shrub_util.qotd.qotd import QuoteOfTheDay
from shrub_archi.repository_merger import RepositoryMerger



from shrub_archi.identity_resolver import IdentityResolver, NaiveIdentityComparator, ResolutionStore
from shrub_archi.repository import Repository

usage = """
    Archi Shrubbery, assumes:
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

def do_create_resolution_file(repo1, repo2, resolution_store_location):
    merger = RepositoryMerger(Repository(repo1), Repository(repo2), resolution_store_location)

    merger.do_merge()
    res_store = ResolutionStore(resolution_store_location)
    res_store.resolutions = merger.identity_resolver.resolved_ids
    res_store.write("dry_run")


logging.configure_console()
if __name__ == "__main__":
    def do_print_usage():
        qotd = QuoteOfTheDay().get_quote()
        print(usage + f"\n    {qotd['quote']} - {qotd['source']}")

    args = Arguments()
    help = args.has_arg("help")
    dry_run = args.has_arg("dry-run") or True
    # repo1 = args.get_arg("repo1", "/Users/mwa17610/Library/Application Support/Archi4/model-repository/gemma-archi-repository/model")
    # repo2 = args.get_arg("repo2", "/Users/mwa17610/Library/Application Support/Archi4/model-repository/gemma-archi-repository/model" )
    repo1 = args.get_arg("repo1","/Users/mwa17610/Library/Application Support/Archi4/model-repository/entrmo_archi/model")
    repo2 = args.get_arg("repo2",
        "/Users/mwa17610/Library/Application Support/Archi4/model-repository/entrmo_archi/model")
    resolution_store_location = args.get_arg("folder","/tmp")

    if help:
        do_print_usage()
    elif dry_run:
        do_create_resolution_file(repo1, repo2, resolution_store_location=resolution_store_location)
    else:
        do_create_resolution_file(repo1, repo2)