import shrub_util.core.logging as logging
from shrub_archi.repository.repository import Repository, XmiArchiRepository, CoArchiRepository, ViewRepositoryFilter
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
    Function:
    - import    
    Parameters:    
    - source: source XMI file location
    - target: target XMI file location
    - workdir: work directory
    - cutoff: cut off for comparison
    - resolutions: name of the resolutions file (without .json) in the work directory
    
    Mode - create graph
    Function:
    - graph
    Parameters:    
    - source: source XMI file location
    - workdir: output directory
    
    TODO:
    - feature: Option to overwrite target repository identities
"""


def create_repository(location: str) -> Repository:
    if location.lower().endswith((".archimate", ".xml")):
        return XmiArchiRepository(location)
    else:
        return CoArchiRepository(location)


def get_resolution_name(repo: Repository, resolution_name):
    return resolution_name if resolution_name else repo.name


def do_create_resolution_file(importer, resolution_store_location, resolution_name: str = None) -> bool:
    created = False
    res_store = ResolutionStore(resolution_store_location)

    res_store.read(get_resolution_name(importer.source_repo, resolution_name))
    importer.do_resolve()
    res_store.apply_to(importer.resolutions)
    if do_show_resolve_ui(importer.resolutions):
        res_store.resolutions = importer.resolutions
        res_store.write(get_resolution_name(importer.source_repo, resolution_name))
        created = True
    return created


def do_import(importer, resolution_store_location, resolution_name: str = None):
    res_store = ResolutionStore(resolution_store_location)
    res_store.read(get_resolution_name(importer.source_repo, resolution_name))
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
    source = args.get_arg("source")
    target = args.get_arg("target")
    work_dir = args.get_arg("workdir")
    function_import = args.has_arg("import")
    function_create_graph = args.has_arg("graph")
    cutoff_score = args.get_arg("cutoff", 85)
    resolution_name = args.get_arg("resolutions", None)

    # do_show_select_furniture_test()
    if help:
        do_print_usage()
    elif function_import:
        target_repo = create_repository(target)
        source_repo = create_repository(source)
        source_repo.read()
        view_repo_filter = ViewRepositoryFilter(do_select_views(source_repo))
        importer = XmiArchiRepositoryImporter(target_repo=target_repo, source_repo=source_repo,
                                              source_filter=view_repo_filter, compare_cutoff_score=cutoff_score)
        if do_create_resolution_file(importer, resolution_store_location=work_dir, resolution_name=resolution_name):
            do_import(importer, resolution_store_location=work_dir, resolution_name=resolution_name)

    elif function_create_graph:
        source_repo = create_repository(source)
        source_repo.read()
        RepositoryGrapher().create_graph(source_repo, work_dir=work_dir)
