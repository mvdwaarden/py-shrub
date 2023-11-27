import shrub_util.core.logging as logging
from shrub_archi.repository.repository import Repository, XmiArchiRepository, \
    CoArchiRepository, ViewRepositoryFilter
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

    Mode - import source repository into target repository    
    Parameters:
    - source: source XMI file location
    - target: target XMI file location
    
"""


def create_repository(location: str) -> Repository:
    if location.lower().endswith((".archimate", ".xml")):
        return XmiArchiRepository(location)
    else:
        return CoArchiRepository(location)


def do_create_resolution_file(importer, resolution_store_location,
                              resolution_name="dry_run") -> bool:
    created = False
    res_store = ResolutionStore(resolution_store_location)
    res_store.read(resolution_name)
    importer.do_resolve()
    res_store.apply_to(importer.resolutions)
    if do_show_resolve_ui(importer.resolutions):
        res_store.resolutions = importer.resolutions
        res_store.write(resolution_name)
        created = True
    return created


def do_import(importer, resolution_store_location, resolution_name="dry_run"):
    res_store = ResolutionStore(resolution_store_location)
    res_store.read(resolution_name)
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
    source = args.get_arg("source", "/tmp/archi_src.xml")
    target = args.get_arg("target", "/tmp/GEMMA 2.xml")
    work_dir = args.get_arg("workdir", "/tmp")
    function_import = args.has_arg("import")

    # do_show_select_furniture_test()
    if help:
        do_print_usage()
    elif function_import:
        target_repo = create_repository(target)
        source_repo = create_repository(source)
        source_repo.read()
        view_repo_filter = ViewRepositoryFilter(do_select_views(source_repo))
        importer = XmiArchiRepositoryImporter(target_repo, source_repo, view_repo_filter)
        if do_create_resolution_file(importer, resolution_store_location=work_dir):
            do_import(importer, resolution_store_location=work_dir)

    else:
        target_repo = create_repository(target)
        source_repo = create_repository(source)
        source_repo.read()
        view_repo_filter = ViewRepositoryFilter(do_select_views(source_repo))
        importer = XmiArchiRepositoryImporter(target_repo, source_repo, view_repo_filter)
        do_create_resolution_file(importer,
                                  resolution_store_location=work_dir)
        RepositoryGrapher.create_graph(target_repo)
