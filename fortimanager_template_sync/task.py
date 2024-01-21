"""FMG Sync Task"""
import logging
import re
from pathlib import Path
from typing import Optional, List

from git import Repo, InvalidGitRepositoryError, GitCommandError

from fortimanager_template_sync.config import FMGSyncSettings
from fortimanager_template_sync.misc import find_all_vars
from fortimanager_template_sync.fmg_api.data import CLITemplate, CLITemplateGroup, Variable

logger = logging.getLogger("fortimanager_template_sync.task")


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
                    parsed_data = self._parse_template_file(name=template_file.name.replace("*.j2", ""), data=data)
                    templates.append(parsed_data)

    @staticmethod
    def _parse_template_file(name: str, data: str) -> CLITemplate:
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
            match = re.search(r"(?<=used vars:)\s*(?P<vars>.*?)\n[\n#-]", header, flags=re.S + re.I)
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
