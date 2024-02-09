"""FMG Sync Task"""
import logging
import re
from copy import copy
from pathlib import Path
from typing import Optional, List, Dict, Any

from git import Repo, InvalidGitRepositoryError, GitCommandError
from more_itertools import first
from pyfortinet.fmg_api.common import F, FilterList

from fortimanager_template_sync.config import FMGSyncSettings
from fortimanager_template_sync.exceptions import FMGSyncVariableException, FMGSyncInvalidStatusException, \
    FMGSyncDeleteError
from fortimanager_template_sync.fmg_api import FMGSync
from fortimanager_template_sync.misc import find_all_vars
from fortimanager_template_sync.fmg_api.data import CLITemplate, CLITemplateGroup, Variable, TemplateTree

logger = logging.getLogger("fortimanager_template_sync.sync_task")


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
    3. check FMG device status list in protected group. If firewalls are not in sync, stop
    4. download FMG templates and template groups from FMG
    5. build list of templates to delete from FMG
    6. build list of templates to upload to FMG
    7. execute changes in FMG

    Attributes:
        settings (FMGSyncSettings): task settings to use
        fmg (FMGSync): FMG instance
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
            FMGSyncVariableException: on invalid variable definitions or conflict
            FMGSyncInvalidStatusException: on invalid device status
        """
        success = False
        # 1. update local repository from remote
        repo = self._update_local_repository()
        if not repo:
            logger.error("Repository couldn't be updated!")
            return success
        # 2. load data from the repo
        repo_data = self._load_local_repository()
        if not repo_data:
            logger.error("Repository couldn't be parsed!")
            return success
        # Initialize FMG connection
        # 3. check FMG device status list in protected group
        #    If firewalls are not in sync, stop
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
            if self.settings.delete_unused_templates:
                to_delete = self._find_unused_templates(repo_data, fmg_data)
                self._delete_templates(to_delete)
            # 6. build list of templates to upload to FMG
            to_upload = self._changed_templates(repo_data, fmg_data)
            if to_upload:
                self._update_fmg_templates(to_upload)
            # 7. execute changes in FMG
            # 8. check firewall statuses
            # 9. deploy changes to firewalls in protected group only
            # 10. check firewall statuses again
            success = True
        finally:
            self.fmg.close(discard_changes=not success)

        return success

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
        logger.info("Load files from repository")
        template_path = Path(self.settings.local_repo) / "templates"
        templates = []
        if template_path.is_dir():
            logger.debug("Loading templates from %s", template_path)
            for template_file in template_path.glob("*.j2"):
                with open(template_file) as fi:
                    data = fi.read()
                    parsed_data = self._parse_template_data(name=template_file.name.replace(".j2", ""), data=data)
                    templates.append(parsed_data)

        pre_run_templates = []
        template_path = Path(self.settings.local_repo) / "pre-run"
        if template_path.is_dir():
            logger.debug("Loading pre-run templates from %s", template_path)
            for template_file in template_path.glob("*.j2"):
                with open(template_file) as fi:
                    data = fi.read()
                    parsed_data = self._parse_template_data(name=template_file.name.replace(".j2", ""), data=data)
                    parsed_data.provision = "enable"
                    pre_run_templates.append(parsed_data)

        template_groups = []
        template_path = Path(self.settings.local_repo) / "template-groups"
        if template_path.is_dir():
            logger.debug("Loading template groups from %s", template_path)
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
        logger.debug("Parsing %s template", name)
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
                error = f"Variable {variable.name} has multiple default values amongst templates!"
                logger.error(error)
                raise FMGSyncVariableException(error)

        return good_variables

    @staticmethod
    def _parse_template_groups_data(
        name: str, data: str, templates: Optional[List[CLITemplate]] = None
    ) -> CLITemplateGroup:
        """Parse template group file"""
        logger.debug("Parsing %s group", name)
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
        logger.info("Gathering firewall statuses in group %s", group)
        statuses = {}
        device_list = self.fmg.get_group_members(group_name=group)
        filters = FilterList()
        for device in device_list.data.get("data", {}).get("object member"):
            filters += F(name=device["name"])
        device_list = self.fmg.get_devices(filters=filters)
        for device_status in device_list.data.get("data"):
            logger.debug(
                "Device %s: dev_status: %s, conf_status: %s, db_status: %s",
                device_status["name"],
                DEV_STATUS.get(device_status["dev_status"]),
                CONF_STATUS.get(device_status["conf_status"]),
                DB_STATUS.get(device_status["db_status"]),
            )

            statuses[device_status["name"]] = {
                "conf_status": CONF_STATUS.get(device_status["conf_status"]),
                "db_status": DB_STATUS.get(device_status["db_status"]),
                "dev_status": DEV_STATUS.get(device_status["dev_status"]),
            }
            if any(value is None for value in statuses[device_status["name"]].values()):
                error = f"Status of {device_status['name']} is invalid: {statuses[device_status['name']]}"
                logger.error(error)
                raise FMGSyncInvalidStatusException(error)
        return statuses

    @staticmethod
    def _ensure_device_statuses(statuses: Dict):
        for device, status in statuses.items():
            if status["conf_status"] not in ("insync",) or status["db_status"] not in ("nomod",):
                error = f"Device '{device}' has problem with status: {status}"
                logger.error(error)
                raise FMGSyncInvalidStatusException(error)

    def _load_fmg_templates(self) -> TemplateTree:
        """Load template data from FMG"""
        logger.info("Loading templates from FMG")
        all_templates = self.fmg.get_cli_templates()
        pre_run_templates = [
            CLITemplate(
                name=template["name"],
                description=template.get("description"),
                provision="enable",
                script=template["script"],
                variables=[Variable(name=var) for var in template["variables"]],
            )
            for template in all_templates.data.get("data")
            if template.get("provision") == 1
        ]
        logger.debug("%d number of pre-run templates loaded", len(pre_run_templates))
        templates = [
            CLITemplate(
                name=template["name"],
                description=template.get("description"),
                provision="enable",
                script=template["script"],
                variables=[Variable(name=var) for var in template["variables"]],
            )
            for template in all_templates.data.get("data")
            if template.get("provision") == 0
        ]
        logger.debug("%d number of templates loaded", len(templates))
        all_groups = self.fmg.get_cli_template_groups()
        template_groups = [
            CLITemplateGroup(
                name=group["name"],
                description=group.get("description"),
                member=group.get("member"),
                variables=[Variable(name=var) for var in group["variables"]],
            )
            for group in all_groups.data.get("data")
        ]
        logger.debug("%d number of pre-run templates loaded", len(template_groups))
        return TemplateTree(templates=templates, pre_run_templates=pre_run_templates, template_groups=template_groups)

    @staticmethod
    def _find_unused_templates(repo_tree: TemplateTree, fmg_tree: TemplateTree) -> TemplateTree:
        """Find undefined or unused templates or groups in FMG

        A template or template group is unused if:

        1. is not assigned to any device or group
        2. does not belong to any template-group
        """
        # pre-run templates cannot be part of any group
        to_del_pre_run = [
            template
            for template in fmg_tree.pre_run_templates
            if template.name not in repo_tree.pre_run_templates and not template.scope_member
        ]
        # find all template groups which may be deleted
        to_del_groups = []
        fmg_groups = copy(fmg_tree.template_groups)
        while True:
            groups = [
                group
                for group in fmg_groups
                if group.name not in repo_tree.template_groups  # not in repo
                and not group.scope_member  # not assigned
                and not any(group.name in other.member for other in fmg_groups if other.member)  # not a member
            ]
            if groups:  # found to be deleted groups
                to_del_groups.extend(groups)
                fmg_groups = [
                    group for group in fmg_groups if group not in groups
                ]  # remove to be deleted groups from list
                # go and check for more groups to be deleted
            else:  # no more to be deleted groups found
                break

        to_del_templates = [
            template
            for template in fmg_tree.templates
            if template.name not in repo_tree.templates
            and not template.scope_member
            and not any(template.name in group.member for group in fmg_groups if group.member)
        ]
        return TemplateTree(pre_run_templates=to_del_pre_run, templates=to_del_templates, template_groups=to_del_groups)

    def _delete_templates(self, templates: TemplateTree):
        """Delete templates and template groups

        Args:
            templates (TemplateTree): template tree object containing CLI templates/groups to delete
        """
        logger.info("Deleting unused templates and template-groups")
        for template_group in templates.template_groups:
            response = self.fmg.delete_cli_template_group(template_group.name)
            if not response.success:
                error = f"Error deleting {template_group.name} template group: {response.data}"
                logger.warning(error)
                raise FMGSyncDeleteError(error)
        for template in templates.pre_run_templates:
            response = self.fmg.delete_cli_template(template.name)
            if not response.success:
                error = f"Error deleting {template.name} template: {response.data}"
                logger.warning(error)
                raise FMGSyncDeleteError(error)
        for template in templates.templates:
            response = self.fmg.delete_cli_template(template.name)
            if not response.success:
                error = f"Error deleting {template.name} template: {response.data}"
                logger.warning(error)
                raise FMGSyncDeleteError(error)

    @staticmethod
    def _changed_templates(repo_data: TemplateTree, fmg_data: TemplateTree) -> TemplateTree:
        """Determine to be updated templates and template groups"""
        # check pre-run templates first
        update_pre_run_templates = []
        for template in repo_data.pre_run_templates:
            # search for existing template
            fmg_template = first((templ for templ in fmg_data.pre_run_templates if template.name == templ.name),
                                 default=None)
            # if template need to be updated, add it to the list
            if fmg_template != template:
                update_pre_run_templates.append(template)
        # check templates
        update_templates = []
        for template in repo_data.templates:
            # search for existing template
            fmg_template = first((templ for templ in fmg_data.templates if template.name == templ.name),
                                 default=None)
            # if template need to be updated, add it to the list
            if fmg_template != template:
                update_templates.append(template)
        # check template groups
        update_template_groups = []
        for group in repo_data.template_groups:
            # search for existing template
            fmg_group = first((grp for grp in fmg_data.template_groups if group.name == grp.name),
                              default=None)
            # if template group need to be updated, add it to the list
            if fmg_group != group:
                update_template_groups.append(group)
        return TemplateTree(
            templates=update_templates,
            pre_run_templates=update_pre_run_templates,
            template_groups=update_template_groups
        )

    def _update_fmg_templates(self, templates: TemplateTree):
        """Update templates and template groups"""
        # need to update variables first

        logger.info("Updating templates")
        for template in templates.pre_run_templates:
            self.fmg.set_cli_template()
