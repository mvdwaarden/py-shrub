import shrub_util.core.logging as logging
from shrub_util.core.arguments import Arguments
from shrub_util.qotd.qotd import QuoteOfTheDay
import concurrent.futures
import itertools
from concurrent.futures import ThreadPoolExecutor



from shrub_archi.identity_resolver import IdentityResolver, NaiveIdentityComparator, Repository


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

def do_test():
    repos = [
        Repository(
            "/Users/mwa17610/Library/Application Support/Archi4/model-repository/entrmo_archi/model"),
        Repository(
            "/Users/mwa17610/Library/Application Support/Archi4/model-repository/entrmo_archi/model")
    ]
    with ThreadPoolExecutor() as exec:
        futures = {
            exec.submit(repo.read):  repo for repo in repos
        }
        for future in concurrent.futures.as_completed(futures):
            repo = future.result()
            print(f"finished {futures[future]} identities {len(repo.identities)}")

    idr = IdentityResolver()
    resolved_ids = list(idr.resolve(repos[0], repos[1], comparator=NaiveIdentityComparator(cutoff_score=0)))
    print(f"resolved ids: {len(resolved_ids)}")
    # for resolved_identity in idr.resolve(repos[0], repos[1]):
    #     if resolved_identity.compare_result.score < 100:
    #         print(resolved_identity)

    for key, group in itertools.groupby(sorted(idr.cache_resolved_ids, key=lambda x: x.compare_result.score), lambda x: x.compare_result.score):
        print (key, len(list(group)))

logging.configure_console()
if __name__ == "__main__":

    def do_print_usage():
        qotd = QuoteOfTheDay().get_quote()
        print(usage + f"\n    {qotd['quote']} - {qotd['source']}")

    args = Arguments()
    help = args.has_arg("help")

    if help:
        do_print_usage()
    else:
        do_test()