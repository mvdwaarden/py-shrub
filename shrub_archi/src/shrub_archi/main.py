import shrub_util.core.logging as logging
from shrub_archi.cmdb.readers.json_reader import cmdb_read_json
from shrub_archi.cmdb.writers.graph_writer import cmdb_write_named_item_graph, GraphType
from shrub_archi.cmdb.writers.json_writer import cmdb_write_json
from shrub_archi.cmdb.cmdb_extract import cmdb_extract
from shrub_archi.cmdb.model.cmdb_model import CmdbLocalView, ConfigurationItem, NamedItem
from shrub_archi.modeling.archi.repository.repository import (Repository, XmiArchiRepository, CoArchiRepository,
                                                              ViewRepositoryFilter, )
from shrub_archi.modeling.archi.repository.repository_graph import RepositoryGrapher
from shrub_archi.modeling.archi.repository.repository_importer import (XmiArchiRepositoryImporter, RepositoryImporter, )
from shrub_archi.modeling.archi.resolver.resolution_store import ResolutionStore
from shrub_archi.modeling.archi.ui.resolution_ui import do_show_resolve_ui
from shrub_archi.modeling.archi.ui.select_diagrams_ui import do_select_diagrams_ui
from shrub_archi.iam.model.iam_model import Authorizations
from shrub_archi.oia.model.oia_model import OiaLocalView
from shrub_archi.oia.oia_extract import oia_extract_authorizations
from shrub_archi.iam.readers.json_reader import iam_read_json
from shrub_archi.iam.writers.json_writer import iam_write_json
from shrub_archi.iam.writers.csv_writer import iam_write_csv
from shrub_archi.oia.oia_api import OiaApi
from shrub_util.core.arguments import Arguments
from shrub_util.qotd.qotd import QuoteOfTheDay
from shrub_archi.oci.oci_api import OciApi
from shrub_archi.oci.oci_extract import oci_extract_users

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
    if location is None or location.lower().endswith((".archimate", ".xml")):
        return XmiArchiRepository(location)
    else:
        return CoArchiRepository(location)


def get_resolution_name(repo: Repository, resolution_name):
    return resolution_name if resolution_name else repo.name


def do_create_resolution_file(importer: RepositoryImporter, resolution_store_location,
                              resolution_name: str = None) -> bool:
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


def do_import(source, target, work_dir):
    target_repo = create_repository(target)
    source_repo = create_repository(source)
    source_repo.read()
    view_repo_filter = ViewRepositoryFilter(do_select_views(source_repo))
    importer = XmiArchiRepositoryImporter(target_repo=target_repo, source_repo=source_repo,
                                          source_filter=view_repo_filter, compare_cutoff_score=cutoff_score, )
    if do_create_resolution_file(importer, resolution_store_location=work_dir, resolution_name=resolution_name, ):
        res_store = ResolutionStore(work_dir)
        res_store.read(get_resolution_name(importer.source_repo, resolution_name))
        importer.do_import()
        importer.target_repo.do_write()
        importer.import_sweep_update_uuids()
        filtered_target = create_repository(importer.target_repo.get_dry_run_location())
        filtered_target.read()
        filtered_view_repo_filter = ViewRepositoryFilter(
            list([view for view in filtered_target.views if view_repo_filter.contains(view)]))
        exporter = XmiArchiRepositoryImporter(target_repo=create_repository(f"{target}.filtered.xml"),
                                              source_repo=filtered_target, source_filter=filtered_view_repo_filter)
        exporter.do_import()
        exporter.target_repo.do_write()


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
    function_oia = args.get_arg("oia")
    function_oci = args.get_arg("oci")
    function_extract_cmdb = args.has_arg("cmdb")
    function_create_graph = args.has_arg("graph")
    cutoff_score = args.get_arg("cutoff", 85)
    resolution_name = args.get_arg("resolutions", None)
    function_test = args.has_arg("test")
    environment = args.get_arg("env", "ITSM_UAT")
    file = args.get_arg("file")
    emails = args.get_arg("email", "").split(",")
    cmdb_api = args.get_arg("cmdb-api")
    use_local_view = args.has_arg("use-local-view")
    source = args.get_arg("source")
    node_exclusion = args.get_arg("skip-ci-nodes", "digitalcertificate, manager").split(",")
    extra_cis = args.get_arg("extra-cis", "").split(",")
    oia_api = args.get_arg("oia-api")
    oci_api = args.get_arg("oci-api")
    export_options = args.get_arg("export-options", "all")
    if help:
        do_print_usage()
    elif function_test:
        from shrub_archi.generator.archi_csv_generator import ArchiCsvGenerator
        import shrub_archi.data.risk.it.it_risk as it_risk
        from shrub_archi.modeling.archi.model import ElementType

        ArchiCsvGenerator().cleanup().write_elements_csv(it_risk.IT_RISKS_ISO_IEC_27001, ElementType.CONSTRAINT)
    elif function_import:
        do_import(source, target, work_dir)
    elif function_create_graph:
        source_repo = create_repository(source)
        source_repo.read()
        RepositoryGrapher().create_graph(source_repo, work_dir=work_dir)
    elif function_oia:
        if use_local_view:
            local_view = OiaLocalView()
            iam_read_json(local_view, file)
            print(local_view.to_dict())
        elif function_oia == "export":
            local_view = oia_extract_authorizations(environment=environment, oia_api=oia_api)
            iam_write_json(local_view=local_view, file=file)
            iam_write_csv(local_view=local_view, file=file)
        elif function_oia == "update-authorizations":
            local_view = OiaLocalView()
            iam_read_json(local_view=local_view, file=file)
            auths = Authorizations(local_view.map_authorizations.values())
            api = OiaApi(environment=environment, oia_api=oia_api, base_url=oia_api)
            # only update authorizations for user accounts (NOT for local accounts)
            for identity in [identity for identity in auths.get_identities() if identity.email]:
                api.update_identity(identity, authorizations=auths)
        elif function_oia == "connect":
            from shrub_archi.connectors.oracle.token import oracle_oia_get_token
            for env in environment.split(","):
                try:
                    token = oracle_oia_get_token(application=env)
                    print(token.access_token[:20])
                except Exception as ex:
                    print(f"getting token for environment {env} failed")
    elif function_oci:
        if function_oci == "load-test":
            api = OciApi(environment=environment, base_url=oci_api)
            api.load_test()
        elif function_oci == "export":
            local_view = oci_extract_users(environment=environment, base_url=oci_api)
            iam_write_json(local_view=local_view, file=file)
            iam_write_csv(local_view=local_view, file=file)
    elif function_extract_cmdb:
        def node_filter(node: NamedItem) -> bool:
            if isinstance(node, ConfigurationItem) and node.type:
                return node.type.lower() not in node_exclusion
            else:
                return node.__class__.__name__.lower() not in node_exclusion
        if use_local_view:
            local_view = CmdbLocalView()
            cmdb_read_json(local_view, file)
            cmdb_write_named_item_graph(local_view, GraphType.GRAPHML, file, node_filter=node_filter)
            cmdb_write_named_item_graph(local_view, GraphType.GRAPHML, f"{file}-without-refs", node_filter=node_filter,
                                        include_object_reference=False)
            cmdb_write_named_item_graph(local_view, GraphType.CYPHER, file, node_filter=node_filter)
            cmdb_write_named_item_graph(local_view, GraphType.DOT, file, node_filter=node_filter)
            cmdb_write_named_item_graph(local_view, GraphType.DOT, f"{file}-without-refs", node_filter=node_filter,
                                        include_object_reference=False)
        else:
            local_view = cmdb_extract(environment, emails=emails, cmdb_api=cmdb_api, source=source, extra_cis=extra_cis,
                                      test_only=False)
            cmdb_write_json(local_view, file)
            cmdb_write_named_item_graph(local_view, GraphType.DOT, file, node_filter=node_filter)
            cmdb_write_named_item_graph(local_view, GraphType.GRAPHML, file, node_filter=node_filter)
            cmdb_write_named_item_graph(local_view, GraphType.CYPHER, file, node_filter=node_filter)
