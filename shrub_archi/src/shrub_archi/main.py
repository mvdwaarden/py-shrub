import shrub_util.core.logging as logging
from shrub_archi.repository.repository import Repository, XmiArchiRepository, \
    CoArchiRepository
from shrub_archi.repository.repository_graph import RepositoryGrapher
from shrub_archi.repository.repository_importer import XmiArchiRepositoryImporter
from shrub_archi.resolver.resolution_store import ResolutionStore
from shrub_archi.ui.resolution_ui import do_show_resolve_ui
from shrub_archi.ui.select_diagrams_ui import do_select_diagrams_ui
from shrub_util.core.arguments import Arguments
from shrub_util.qotd.qotd import QuoteOfTheDay

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


def create_repository(location: str) -> Repository:
    if location.lower().endswith((".archimate", ".xml")):
        return XmiArchiRepository(location)
    else:
        return CoArchiRepository(location)


def do_create_resolution_file(repo1, repo2, repo2_filter, resolution_store_location,
                              resolution_name="dry_run") -> bool:
    created = False
    merger = XmiArchiRepositoryImporter(repo1, repo2, repo2_filter)
    res_store = ResolutionStore(resolution_store_location)
    res_store.read(resolution_name)
    merger.do_resolve()
    res_store.apply_to(merger.resolutions)
    if do_show_resolve_ui(merger.resolutions):
        res_store.resolutions = merger.resolutions
        res_store.write(resolution_name)
        created = True
    return created


def do_import(target_repo, source_repo, source_filter, resolution_store_location,
              resolution_name="dry_run"):
    res_store = ResolutionStore(resolution_store_location)
    res_store.read(resolution_name)
    importer = XmiArchiRepositoryImporter(target_repo, source_repo, source_filter,
                                          res_store)
    importer.do_import()
    importer.target_repo.do_write()
    importer.import_sweep_update_uuids()


def do_select_views(repo: Repository):
    selected, views = do_select_diagrams_ui(repo.views)

    return views


logging.configure_console()
if __name__ == "__main__":
    def do_print_usage():
        qotd = QuoteOfTheDay().get_quote()
        print(usage + f"\n    {qotd['quote']} - {qotd['source']}")


    args = Arguments()
    help = args.has_arg("help")
    dry_run = args.has_arg("dry-run") or True
    repo1 = args.get_arg("repo1",
                         "/Users/mwa17610/Library/Application Support/Archi4/model-repository/gemma-archi-repository/model")
    repo2 = args.get_arg("repo2",
                         "/Users/mwa17610/Library/Application Support/Archi4/model-repository/gemma-archi-repository/model")
    repo1 = args.get_arg("repo1",
                         "/Users/mwa17610/Library/Application Support/Archi4/model-repository/archi_1/model")
    # repo2 = args.get_arg("repo2", "/tmp/test/archi/model")
    repo1 = args.get_arg("repo1", "/tmp/archi_src.xml")
    repo2 = args.get_arg("repo2", "/tmp/GEMMA 2.xml")
    resolution_store_location = args.get_arg("folder", "/tmp")
    # do_show_select_furniture_test()
    if help:
        do_print_usage()
    elif dry_run:
        target_repo = create_repository(repo1)
        source_repo = create_repository(repo2)
        source_repo.read()
        views = do_select_views(source_repo)
        if do_create_resolution_file(target_repo, source_repo, views,
                                     resolution_store_location=resolution_store_location):
            do_import(target_repo, source_repo, views,
                      resolution_store_location=resolution_store_location)


    else:
        target_repo = create_repository(repo1)
        source_repo = create_repository(repo2)
        source_repo.read()
        views = do_select_views(source_repo)
        do_create_resolution_file(target_repo, source_repo, views,
                                  resolution_store_location=resolution_store_location)
        RepositoryGrapher.create_graph(target_repo)
