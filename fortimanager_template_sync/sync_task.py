"""FMG Sync Task"""

import json
import logging
import re
from copy import copy
from pathlib import Path
from typing import List, Optional

from git import GitCommandError, InvalidGitRepositoryError, Repo
from more_itertools import first

from fortimanager_template_sync.common_task import CommonTask
from fortimanager_template_sync.exceptions import FMGSyncDeleteError
from fortimanager_template_sync.fmg_api import FMGSync
from fortimanager_template_sync.fmg_api.data import CLITemplate, CLITemplateGroup, TemplateTree, Variable
from fortimanager_template_sync.misc import find_all_vars, sanitize_variables

logger = logging.getLogger("fortimanager_template_sync.sync_task")


class FMGSyncTask(CommonTask):
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

    def run(self) -> bool:
        """Run sync task

        Returns:
            (bool): True if sync task succeeded, False otherwise
        """
        success = False
        changes = False
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
            fmg_templates = self._load_fmg_templates()
            # 5. build list of templates to delete from FMG
            to_delete = None
            if self.settings.delete_unused_templates:
                to_delete = self._find_unused_templates(repo_data, fmg_templates)
            # 6. build list of templates to upload to FMG
            to_upload = self._changed_templates(repo_data, fmg_templates)
            # 7. execute changes in FMG
            if to_delete:
                changes = self._delete_templates(to_delete)
            elif self.settings.delete_unused_templates:
                logger.info("No templates to delete")
            if to_upload:
                changes = self._update_fmg_templates(templates=to_upload, fmg_templates=fmg_templates) or changes
            else:
                logger.info("No templates to update!")
            success = True
        except Exception as err:
            logger.error(err)
        finally:
            if changes and self.settings.prod_run:
                logger.info("Changes applied successfully")
            else:
                logger.info("No changes happened")
            if self.fmg:
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
        See [docs](../user_guide/repository.md) for additional information.

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
        logger.debug("Parsing '%s' template", name)
        description = ""
        variables = []
        scope_members = None
        # gather metadata
        match = re.match(r"^{#(.*?)#}", data, re.S + re.I)
        if match:
            header = match.group(1)
            description = header.splitlines()[0].strip()
            # parse used variables
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
            # parse assignments
            match = re.search(r"(?<=assigned to:)\s*(?P<assigned>.*?)\n", header, flags=re.S + re.I)
            if match and match.group("assigned"):
                try:
                    assigned = json.loads(match.group("assigned"))
                    scope_members = assigned if isinstance(assigned, list) else [assigned]
                except json.decoder.JSONDecodeError:
                    logger.warning("Assignment target of '%s' at template '%s' is not valid JSON!")
                    raise

        template_vars = find_all_vars(data)
        # filter out built-in datasource
        template_vars = [var for var in template_vars if not var.startswith("DVMDB")]
        # filter out already documented variables
        template_vars = [var for var in template_vars if var not in variables]
        for template_var in template_vars:
            variables.append(Variable(name=template_var))

        return CLITemplate(
            name=name, description=description, variables=variables, script=data, scope_member=scope_members
        )

    @staticmethod
    def _parse_template_groups_data(
        name: str, data: str, templates: Optional[List[CLITemplate]] = None
    ) -> CLITemplateGroup:
        """Parse template group file"""
        logger.debug("Parsing '%s' group", name)
        description = None
        members = []
        variables = []
        scope_members = None
        # gather metadata
        match = re.match(r"^{#(.*?)#}", data, re.S + re.I)
        if match:
            header = match.group(1)
            description = header.splitlines()[0].strip()
            # parse assignments
            match = re.search(r"(?<=assigned to:)\s*(?P<assigned>.*?)\n", header, flags=re.S + re.I)
            if match and match.group("assigned"):
                try:
                    assigned = json.loads(match.group("assigned"))
                    scope_members = assigned if isinstance(assigned, list) else [assigned]
                except json.decoder.JSONDecodeError:
                    logger.warning("Assignment target of '%s' at template '%s' is not valid JSON!")
                    raise
        # gather members
        for match in re.finditer(r"{%\s*include\s*\"templates/(?P<member>.*).j2\"\s*%}", data, re.M):
            members.append(match.group("member"))
        # gather variables
        for template in templates:
            variables.extend(template.variables)  # flat out lists
        # deduplicate and sanity check on variables
        variables = sanitize_variables(variables=variables)

        return CLITemplateGroup(
            name=name, description=description, member=members, variables=variables, scope_member=scope_members
        )

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
        logger.debug("%d pre-run templates loaded", len(pre_run_templates))
        templates = [
            CLITemplate(
                name=template["name"],
                description=template.get("description"),
                script=template["script"],
                variables=[Variable(name=var) for var in template["variables"]],
            )
            for template in all_templates.data.get("data")
            if template.get("provision") == 0
        ]
        logger.debug("%d templates loaded", len(templates))
        all_groups = self.fmg.get_cli_template_groups()
        template_groups = [
            CLITemplateGroup(
                name=group["name"],
                description=group.get("description"),
                member=group.get("member"),
                variables=[Variable(name=var) for var in group["variables"]],
                scope_member=group.get("scope member"),
            )
            for group in all_groups.data.get("data")
        ]
        logger.debug("%d template groups loaded", len(template_groups))
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
            if self.settings.prod_run:
                logger.info("Deleting template group '%s'", template_group.name)
                response = self.fmg.delete_cli_template_group(template_group.name)
                if not response.success:
                    error = f"Error deleting '{template_group.name}' template group: {response.data}"
                    logger.warning(error)
                    raise FMGSyncDeleteError(error)
            else:
                logger.info("TEST - deleting template group '%s'", template_group.name)
        for template in templates.pre_run_templates + templates.templates:
            if self.settings.prod_run:
                logger.info("Deleting template '%s'", template.name)
                response = self.fmg.delete_cli_template(template.name)
                if not response.success:
                    error = f"Error deleting '{template.name}' template: {response.data}"
                    logger.warning(error)
                    raise FMGSyncDeleteError(error)
            else:
                logger.info("TEST - deleting template '%s'", template.name)

    @staticmethod
    def _changed_templates(repo_data: TemplateTree, fmg_data: TemplateTree) -> TemplateTree:
        """Determine to be updated templates and template groups"""
        # check pre-run templates first
        update_pre_run_templates = []
        for template in repo_data.pre_run_templates:
            # search for existing template
            fmg_template = first(
                (templ for templ in fmg_data.pre_run_templates if template.name == templ.name), default=None
            )
            # if template need to be updated, add it to the list
            if fmg_template != template:
                update_pre_run_templates.append(template)
        # check templates
        update_templates = []
        for template in repo_data.templates:
            # search for existing template
            fmg_template = first((templ for templ in fmg_data.templates if template.name == templ.name), default=None)
            # if template need to be updated, add it to the list
            if fmg_template != template:
                update_templates.append(template)
        # check template groups
        update_template_groups = []
        for group in repo_data.template_groups:
            # search for existing template
            fmg_group = first((grp for grp in fmg_data.template_groups if group.name == grp.name), default=None)
            # if template group need to be updated, add it to the list
            if fmg_group != group:
                update_template_groups.append(group)
        return TemplateTree(
            templates=update_templates,
            pre_run_templates=update_pre_run_templates,
            template_groups=update_template_groups,
        )

    def _update_fmg_templates(self, templates: TemplateTree, fmg_templates: TemplateTree) -> bool:
        """Update templates and template groups"""
        # need to update variables first
        had_changed = False
        to_add_vars = [variable for variable in templates.variables if variable.name not in fmg_templates.variables]
        if to_add_vars:
            logger.info("Adding missing variables")
        for variable in to_add_vars:
            if self.settings.prod_run:
                result = self.fmg.set_fmg_variable(**variable.model_dump(by_alias=True))
                if not result.success:
                    logger.error("Error adding variable '%s'", variable.name)
                    continue
            else:
                logger.info("TEST - Adding variable '%s'", variable.name)
            had_changed = True

        logger.info("Updating templates")
        for template in (*templates.pre_run_templates, *templates.templates):
            if self.settings.prod_run:
                result = self.fmg.set_cli_template(**template.model_dump(by_alias=True))
                if not result.success:
                    logger.error("Error updating template '%s'", template.name)
                    continue
                elif template.scope_member:
                    self.fmg.assign_cli_template(template.name, template.scope_member)
            else:
                logger.info("TEST - Updating template '%s'", template.name)
            had_changed = True

        for template_group in templates.template_groups:
            if self.settings.prod_run:
                result = self.fmg.set_cli_template_group(**template_group.model_dump(by_alias=True))
                if not result.success:
                    logger.error("Error updating template group '%s'", template_group.name)
                    continue
                elif template_group.scope_member:
                    self.fmg.assign_cli_template_group(template_group.name, template_group.scope_member)
            else:
                logger.info("TEST - Updating template_group '%s'", template_group.name)
            had_changed = True
        return had_changed
