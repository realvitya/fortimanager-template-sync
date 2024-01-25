"""FMG Sync Task"""
import logging
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

from git import Repo, InvalidGitRepositoryError, GitCommandError
from more_itertools import first
from pydantic.dataclasses import dataclass
from pyfortinet.fmg_api.common import F, FilterList

from fortimanager_template_sync.config import FMGSyncSettings
from fortimanager_template_sync.exceptions import FMGSyncVariableException, FMGSyncInvalidStatusException
from fortimanager_template_sync.fmg_api import FMGSync
from fortimanager_template_sync.misc import find_all_vars
from fortimanager_template_sync.fmg_api.data import CLITemplate, CLITemplateGroup, Variable

logger = logging.getLogger("fortimanager_template_sync.task")


@dataclass
class TemplateTree:
    """Template data structure"""

    pre_run_templates: List[CLITemplate]
    templates: List[CLITemplate]
    template_groups: List[CLITemplateGroup]


DEV_STATUS = {
    0: "none",
    "none": "none",
    1: "unknown",
    "unknown": "unknown",
    2: "checkedin",
    "checkedin": "checkedin",
    3: "inprogress",
    "inprogress": "inprogress",
    4: "installed",
    "installed": "installed",
    5: "aborted",
    "aborted": "aborted",
    6: "sched",
    "sched": "sched",
    7: "retry",
    "retry": "retry",
    8: "canceled",
    "canceled": "canceled",
    9: "pending",
    "pending": "pending",
    10: "retrieved",
    "retrieved": "retrieved",
    11: "changed_conf",
    "changed_conf": "changed_conf",
    12: "sync_fail",
    "sync_fail": "sync_fail",
    13: "timeout",
    "timeout": "timeout",
    14: "rev_revert",
    "rev_revert": "rev_revert",
    15: "auto_updated",
    "auto_updated": "auto_updated",
}

DB_STATUS = {
    0: "unknown",
    "unknown": "unknown",
    1: "nomod",
    "nomod": "nomod",
    2: "mod",
    "mod": "mod",
}

CONF_STATUS = {
    0: "unknown",
    "unknown": "unknown",
    1: "insync",
    "insync": "insync",
    2: "outofsync",
    "outofsync": "outofsync",
}


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

    def __init__(self, settings: FMGSyncSettings, fmg: Optional[FMGSync] = None):
        """Initialize task

        Args:
            settings: task settings
            fmg: FMG connection if there is any
        """
        self.settings = settings
        self.fmg = fmg

    def run(self):
        """Run task

        Raises:
            FMGSyncException

        """
        # 1. update local repository from remote
        repo = self._update_local_repository()
        # 2. load data from the repo
        repo_data = self._load_local_repository()
        # Initialize FMG connection
        # 3. check FMG device status list in protected group
        #    If firewalls are not in sync, stop
        success = False
        try:
            if not self.fmg:
                self.fmg = FMGSync(
                    base_url=self.settings.fmg_url,
                    username=self.settings.fmg_user,
                    password=self.settings.fmg_pass,
                    adom=self.settings.fmg_adom,
                    verify=self.settings.fmg_verify,
                ).open()
            self._ensure_device_statuses(self._get_firewall_statuses(self.settings.protected_fw_group))
        # 4. download FMG templates and template groups from FMG
            fmg_data = self._load_fmg_templates()
        # 5. build list of templates to delete from FMG
        # 6. build list of templates to upload to FMG
        # 7. execute changes in FMG
        # 8. check firewall statuses
        # 9. deploy changes to firewalls in protected group only
        # 10. check firewall statuses again
            success = True
        finally:
            self.fmg.close(discard_changes=not success)

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

    def _get_firewall_statuses(self, group: str) -> Dict[str, Dict[str, Any]]:
        """Gather firewall statuses in the specified group"""
        statuses = {}
        device_list = self.fmg.get_group_members(group_name=group)
        filters = FilterList()
        for device in device_list.data.get("data", {}).get("object member"):
            # statuses[device["name"]] = {"vdom": device["vdom"]}
            filters += F(name=device["name"])
        device_list = self.fmg.get_devices(filters=filters)
        for device_status in device_list.data.get("data"):
            statuses[device_status["name"]] = {
                "conf_status": CONF_STATUS.get(device_status["conf_status"]),
                "db_status": DB_STATUS.get(device_status["db_status"]),
                "dev_status": DEV_STATUS.get(device_status["dev_status"]),
            }
            if any(value is None for value in statuses[device_status["name"]]):
                raise FMGSyncInvalidStatusException(f"Status of {device_status['name']} is invalid: {statuses[device_status['name']]}")
        return statuses

    @staticmethod
    def _ensure_device_statuses(statuses: Dict):
        for device, status in statuses.items():
            if status["conf_status"] not in ("insync",) or \
               status["db_status"] not in ("nomod",):
                raise FMGSyncInvalidStatusException(f"Device '{device}' has problem with status: {status}")

    def _load_fmg_templates(self) -> TemplateTree:
        """Load template data from FMG"""
        all_templates = self.fmg.get_cli_templates()
        pre_run_templates = [
            CLITemplate(
                name=template["name"],
                description=template.get("description"),
                provision="enable",
                script=template["script"],
                variables=[Variable(name=var) for var in template["variables"]]
            )
            for template in all_templates.data.get("data") if template.get("provision") == 1
        ]
        templates = [
            CLITemplate(
                name=template["name"],
                description=template.get("description"),
                provision="enable",
                script=template["script"],
                variables=[Variable(name=var) for var in template["variables"]]
            )
            for template in all_templates.data.get("data") if template.get("provision") == 0
        ]
        all_groups = self.fmg.get_cli_template_groups()
        template_groups = [
            CLITemplateGroup(
                name=group["name"],
                description=group.get("description"),
                member=group.get("member"),
                variables=[Variable(name=var) for var in group["variables"]]
            )
            for group in all_groups.data.get("data")
        ]
        return TemplateTree(templates=templates, pre_run_templates=pre_run_templates, template_groups=template_groups)
