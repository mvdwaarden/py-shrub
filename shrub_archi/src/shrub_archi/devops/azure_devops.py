import requests
from requests.auth import AuthBase, HTTPBasicAuth
from shrub_util.core.secrets import Secrets
from typing import TypeVar


class DevOpsItem:
    def __init__(self):
        self.id: str = None
        self.url: str = None
        self.name: str = None

class Project(DevOpsItem):
    def __init__(self):
        super().__init__()


class Team(DevOpsItem):
    def __init__(self):
        super().__init__()

class WorkItem(DevOpsItem):
    def __init__(self):
        super().__init__()

class AzureDevOpsLocalView:
    def __init__(self):
        self.projects = {}
        self.teams = {}
        self.work_items = {}

    def resolve_project(self, prj: Project) -> Project:
        if prj.name in self.projects:
            result = self.projects[prj.name]
        else:
            self.projects[prj.name] = prj
            result = prj
        return result

    def resolve_team(self, team: Team) -> Team:
        if team.name in self.teams:
            result = self.teams[team.name]
        else:
            self.teams[team.name] = team
            result = team
        return result

    def resolve_work_item(self, work_item: WorkItem) -> WorkItem:
        if work_item.id in self.work_items:
            result = self.work_items[work_item.id]
        else:
            self.work_items[work_item.id] = work_item
            result = work_item
        return result

T = TypeVar("T")

class AzureDevOpsApiObjectFactory:
    def __init__(self, local_view: AzureDevOpsLocalView):
        self.local_view = local_view

    def _assign_default_devops_item_values_from_value_json(self, value_dict: dict, doi: T) -> T:
        if 'id' in value_dict:
            doi.id = value_dict['id']
        if 'name' in value_dict:
            doi.name = value_dict['name']
        if 'url' in value_dict:
            doi.url = value_dict['url']

        return doi

    def get_projects_from_get_projects_result_json(self, json_dict: dict) -> list:
        result = []
        if int(json_dict['count']) > 0:
            for i in range(0, int(json_dict['count'])):
                value_dict = json_dict['value'][i]
                prj = self._assign_default_devops_item_values_from_value_json(value_dict, Project())
                resolved_project = self.local_view.resolve_project(prj)

                result.append(resolved_project)
        return result

    def get_teams_from_get_project_teams_result_json(self, json_dict: dict) -> list:
        result = []
        if int(json_dict['count']) > 0:
            for i in range(0, int(json_dict['count'])):
                value_dict = json_dict['value'][i]
                team = self._assign_default_devops_item_values_from_value_json(value_dict, Team())
                resolved_team = self.local_view.resolve_team(team)

                result.append(resolved_team)
        return result

    def get_work_items_from_work_items_by_wiql(self, json_dict) -> list:
        result = []
        if 'workItems' in json_dict:
            for value_dict in json_dict['workItems']:
                wi = self._assign_default_devops_item_values_from_value_json(value_dict, WorkItem())
                resolved_work_item = self.local_view.resolve_work_item(wi)
                result.append(resolved_work_item)
        return result


class AzureDevOpsApi:
    FUNCTION_PROJECTS = "{organisation}/_apis/projects"
    FUNCTION_PROJECT_TEAMS =  FUNCTION_PROJECTS + "/{project.id}/teams"
    FUNCTION_PROJECT_WORK_ITEMS = "{organisation}/{project.id}/{team.id}/_apis/wit/wiql?{version}"

    def __init__(self, base_url: str = None, organisation: str = None):
        self.base_url = base_url if base_url else "https://dev.azure.com"
        self.organisation = organisation
        self.PAT = Secrets().get_section(f"Token-AzDevOps-{self.organisation}-PAT").get_setting("Secret")

    def _get_url(self, function: str, **args):
        cloned_args = {k: args[k] for k in args.keys()}
        cloned_args["organisation"] = self.organisation.lower()
        cloned_args["version"] = "api-version=7.1"
        url = f"{self.base_url}/{function.format(**cloned_args)}"
        return url

    def _get_authorization(self) -> AuthBase:
        return HTTPBasicAuth('', self.PAT)

    def get_projects(self) -> dict:
        response = requests.get(self._get_url(self.FUNCTION_PROJECTS), auth=self._get_authorization())
        return response.json()

    def get_project_teams(self, project: Project) -> dict:
        response = requests.get(self._get_url(self.FUNCTION_PROJECT_TEAMS, project=project), auth=self._get_authorization())
        return response.json()

    def get_work_items(self, project: Project, team: Team, max_result: int=-1):
        query = "select * from workitems where system.workitemtype == 'Epic' "
        response = requests.post(self._get_url(self.FUNCTION_PROJECT_WORK_ITEMS, project=project, team=team) +
                                 (f"&$top={max_result}" if max_result > 0 else ""),
                                json={"query": f"{query}"},
                                auth=self._get_authorization())
        return response.json()


def azure_dev_ops_get_projects(api: AzureDevOpsApi, local_view: AzureDevOpsLocalView):
    factory = AzureDevOpsApiObjectFactory(local_view)
    return factory.get_projects_from_get_projects_result_json(api.get_projects())

def azure_dev_ops_get_project_teams(api: AzureDevOpsApi, local_view: AzureDevOpsLocalView, project: Project):
    factory = AzureDevOpsApiObjectFactory(local_view)
    return factory.get_teams_from_get_project_teams_result_json(api.get_project_teams(project))


def azure_dev_ops_get_work_items_for_project(api: AzureDevOpsApi, local_view: AzureDevOpsLocalView, project: Project, team: Team,max_result=-1):
    factory = AzureDevOpsApiObjectFactory(local_view)
    return factory.get_work_items_from_work_items_by_wiql(api.get_work_items(project=project, team=team, max_result=max_result))
