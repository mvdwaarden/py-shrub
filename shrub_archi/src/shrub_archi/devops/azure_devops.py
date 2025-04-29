import requests
from requests.auth import AuthBase, HTTPBasicAuth
from shrub_util.core.secrets import Secrets


class Project:
    def __init__(self):
        self.name: str = None


class WorkItem:
    def __init__(self):
        self.name: str = None


class AzureDevOpsLocalView:
    def __init__(self):
        self.projects = {}
        self.work_items = {}

    def resolve_project(self, prj: Project):
        if prj.name in self.projects:
            result = self.projects[prj.name]
        else:
            self.projects[prj.name] = prj
            result = prj
        return result


class AzureDevOpsApiObjectFactory:
    def __init__(self, local_view: AzureDevOpsLocalView):
        self.local_view = local_view


    def get_projects_from_get_projects_result_json(self, json_dict: dict) -> list:
        result = []
        if int(json_dict['count']) > 0:
            for i in range(0, int(json_dict['count'])):
                prj = Project()
                prj.name = json_dict['value'][i]['name']
                resolved_project = self.local_view.resolve_project(prj)

                result.append(resolved_project)
        return result

    def get_work_items_from_work_items_for_project_result_json(self, json_dict) -> list:
        result = []

        return result


class AzureDevOpsApi:
    FUNCTION_PROJECTS = "{organisation}/_apis/projects?{version}"
    FUNCTION_PROJECT_WORK_ITEMS = "{organisation}/{project}/_apis/_workitems?{version}"

    def __init__(self, base_url: str = None, organisation: str = None):
        self.base_url = base_url if base_url else "https://dev.azure.com"
        self.organisation = organisation
        self.PAT = Secrets().get_section(f"Token-AzDevOps-{self.organisation}-PAT").get_setting("Secret")

    def _get_url(self, function: str, **args):
        cloned_args = {k: args[k] for k in args.keys()}
        cloned_args["organisation"] = self.organisation.lower()
        cloned_args["version"] = "api-version=6.0"
        url = f"{self.base_url}/{function.format(**cloned_args)}"
        return url

    def _get_authorization(self) -> AuthBase:
        return HTTPBasicAuth('', self.PAT)

    def get_projects(self) -> dict:
        response = requests.get(self._get_url(self.FUNCTION_PROJECTS), auth=self._get_authorization())
        return response.json()

    def get_work_items(self, project: str):
        response = requests.get(self._get_url(self.FUNCTION_PROJECT_WORK_ITEMS, project=project),
                                auth=self._get_authorization())
        return response


def azure_dev_ops_get_projects(api: AzureDevOpsApi, local_view: AzureDevOpsLocalView):
    factory = AzureDevOpsApiObjectFactory(local_view)
    return factory.get_projects_from_get_projects_result_json(api.get_projects())


def azure_dev_ops_get_work_items_for_project(api: AzureDevOpsApi, local_view: AzureDevOpsLocalView, project_name: str):
    factory = AzureDevOpsApiObjectFactory(local_view)
    return factory.get_work_items_from_work_items_for_project_result_json(api.get_work_items(project=project_name))
