"""FMG Sync Task"""
import logging
import re
from pathlib import Path
from typing import Optional, List

from git import Repo, InvalidGitRepositoryError, GitCommandError
from more_itertools import first
from pydantic.dataclasses import dataclass

from fortimanager_template_sync.config import FMGSyncSettings
from fortimanager_template_sync.exceptions import FMGSyncVariableException
from fortimanager_template_sync.misc import find_all_vars
from fortimanager_template_sync.fmg_api.data import CLITemplate, CLITemplateGroup, Variable

logger = logging.getLogger("fortimanager_template_sync.task")


@dataclass
class TemplateTree:
    """Template data structure"""

    pre_run_templates: List[CLITemplate]
    templates: List[CLITemplate]
    template_groups: List[CLITemplateGroup]


class FMGSyncTask:
    """
    Fortimanager Sync Task

    Steps of this task:
    1. update local repository from remote
    2. check if there was a change
    3. check FMG device status list in protected group
       If firewalls are not in sync, stop
    4. download FMG templates and template groups from FMG
    5. build list of templates to delete from FMG
    6. build list of templates to upload to FMG
    7. execute changes in FMG
    8. check firewall statuses
    9. deploy changes to firewalls in protected group only
    10. check firewall statuses again

    Attributes:
        settings (FMGSyncSettings): task settings to use
    """

    def __init__(self, settings: FMGSyncSettings):
        """Initialize task

        Args:
            settings: task settings
        """
        self.settings = settings

    def run(self):
        """Run task

        Raises:
            FMGSyncException
        """
        # 1. update local repository from remote
        repo = self._update_local_repository()
        # 2. load data from the repo
        repo_data = self._load_local_repository()
        # 3. check FMG device status list in protected group
        #    If firewalls are not in sync, stop
        # 4. download FMG templates and template groups from FMG
        # 5. build list of templates to delete from FMG
        # 6. build list of templates to upload to FMG
        # 7. execute changes in FMG
        # 8. check firewall statuses
        # 9. deploy changes to firewalls in protected group only
        # 10. check firewall statuses again

    def _update_local_repository(self) -> Optional[Repo]:
        """Clone or update local repository

        Repository is expected in this format:

        ```
        pre-run/
            pre-run1.j2
            pre-run2.j2
            ...
        templates/
            template1.j2
            template2.j2
            ...
        template-groups/
            group1.j2
            group2.j2
            ...
        ```

        Any other files are ignored. All directories are optional, it's not mandatory to have all of them.
        See [docs](repository.md) for additional information.

        Returns:
            Repository with cloned templates
        """
        logger.info("Checking out template repository")
        try:
            repo = Repo(self.settings.local_repo)
            repo.git.pull()  # download updates
            repo.git.checkout(self.settings.template_branch)
            return repo
        except InvalidGitRepositoryError:  # in case of an empty directory
            logger.info("Cloning template repository")
            repo = Repo.clone_from(
                url=self.settings.template_repo, to_path=self.settings.local_repo, branch=self.settings.template_branch
            )
            return repo
        except GitCommandError:
            logger.error(
                "Can't checkout repo: '%s' branch: '%s'", self.settings.template_repo, self.settings.template_branch
            )
            raise

    def _load_local_repository(self) -> TemplateTree:
        """Load files from repository"""
        template_path = Path(self.settings.local_repo) / "templates"
        templates = []
        if template_path.is_dir():
            for template_file in template_path.glob("*.j2"):
                with open(template_file) as fi:
                    data = fi.read()
                    parsed_data = self._parse_template_data(name=template_file.name.replace(".j2", ""), data=data)
                    templates.append(parsed_data)

        pre_run_templates = []
        template_path = Path(self.settings.local_repo) / "pre-run"
        if template_path.is_dir():
            for template_file in template_path.glob("*.j2"):
                with open(template_file) as fi:
                    data = fi.read()
                    parsed_data = self._parse_template_data(name=template_file.name.replace(".j2", ""), data=data)
                    parsed_data.provision = "enable"
                    pre_run_templates.append(parsed_data)

        template_groups = []
        template_path = Path(self.settings.local_repo) / "template-groups"
        if template_path.is_dir():
            for template_group_file in template_path.glob("*.j2"):
                with open(template_group_file) as fi:
                    data = fi.read()
                    parsed_data = self._parse_template_groups_data(
                        name=template_group_file.name.replace(".j2", ""), data=data, templates=templates
                    )
                    template_groups.append(parsed_data)

        return TemplateTree(templates=templates, pre_run_templates=pre_run_templates, template_groups=template_groups)

    @staticmethod
    def _parse_template_data(name: str, data: str) -> CLITemplate:
        """Parse template script text

        Expected format for metadata (head comment):


        Args:
            name (str): name of the template (file name without extension)
            data (str): raw text of the script file
        """
        description = ""
        variables = []
        # gather metadata
        match = re.match(r"^{#(.*?)#}", data, re.S + re.I)
        if match:
            header = match.group(1)
            description = header.splitlines()[0].strip()
            match = re.search(r"(?<=used vars:)\s*(?P<vars>.*?)\n(?:[\n#-]|$)", header, flags=re.S + re.I)
            if match and match.group("vars"):
                vars_str = match.group("vars")
                vars_list = vars_str.splitlines()
                for var in vars_list:
                    if ":" in var:
                        var_name, var_description = var.split(":", maxsplit=1)
                        var_value = None
                        var_name = var_name.strip()
                        var_description = var_description.strip()
                        match = re.search(r"(?<=default:)\s*(?P<default>.*?)\)", var_description, flags=re.I)
                        if match:
                            var_value = match.group("default")
                    else:
                        var_name, var_description, var_value = var, None, None
                    variables.append(Variable(name=var_name, description=var_description, value=var_value))
        template_vars = find_all_vars(data)
        # filter out built-in datasource
        template_vars = [var for var in template_vars if not var.startswith("DVMDB")]
        # filter out already documented variables
        template_vars = [var for var in template_vars if var not in variables]
        for template_var in template_vars:
            variables.append(Variable(name=template_var))

        return CLITemplate(name=name, description=description, variables=variables, script=data)

    @staticmethod
    def _sanitize_variables(variables: List[Variable]) -> List[Variable]:
        """De-dup and check variables, so they are uniq in name and default value

        Args:
            variables: input list of variables

        Returns:
            list of variables

        Raises:
            FMGSyncVariableException on variable definitions
        """
        good_variables = []
        for variable in variables:
            if variable.name not in good_variables:
                good_variables.append(variable)
                continue
            existing_var = first([var for var in good_variables if var.name == variable.name])
            if variable.value != existing_var.value:
                raise FMGSyncVariableException(f"Variable {variable.name} has multiple default values amongst templates!")

        return good_variables

    @staticmethod
    def _parse_template_groups_data(
        name: str, data: str, templates: Optional[List[CLITemplate]] = None
    ) -> CLITemplateGroup:
        """Parse template group file"""
        description = None
        members = []
        variables = []
        # gather metadata
        match = re.match(r"^{#(.*?)#}", data, re.S + re.I)
        if match:
            header = match.group(1)
            description = header.splitlines()[0].strip()
        # gather members
        for match in re.finditer(r"{%\s*include\s*\"templates/(?P<member>.*).j2\"\s*%}", data, re.M):
            members.append(match.group("member"))
        # gather variables
        for template in templates:
            variables.extend(template.variables)  # flat out lists
        # deduplicate and sanity check on variables
        variables = FMGSyncTask._sanitize_variables(variables=variables)

        return CLITemplateGroup(name=name, description=description, member=members, variables=variables)
