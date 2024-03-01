"""Test helper functions/methods"""

import pytest

from fortimanager_template_sync.exceptions import FMGSyncInvalidStatusException, FMGSyncVariableException
from fortimanager_template_sync.fmg_api.data import CLITemplate, CLITemplateGroup, Variable
from fortimanager_template_sync.misc import sanitize_variables
from fortimanager_template_sync.sync_task import FMGSyncTask, TemplateTree


class TestHelpers:
    """Test helper functions"""

    def test_ensure_device_statuses_good(self):
        statuses = {
            "good_fw": {"conf_status": "insync", "db_status": "nomod", "dev_status": "auto_updated"},
            "good_fw2": {"conf_status": "insync", "db_status": "nomod", "dev_status": "unknown"},
        }

        FMGSyncTask._ensure_device_statuses(statuses)

    def test_ensure_device_statuses_problem(self):
        statuses = {
            "good_fw": {"conf_status": "insync", "db_status": "nomod", "dev_status": "auto_updated"},
            "problematic_fw": {"conf_status": "outofsync", "db_status": "mod", "dev_status": "timeout"},
        }

        with pytest.raises(FMGSyncInvalidStatusException, match=r"problematic_fw"):
            FMGSyncTask._ensure_device_statuses(statuses)

    def test_find_unused_templates(self):
        fmg_tree = TemplateTree(
            pre_run_templates=[
                CLITemplate(name="used", scope_member=[{"name": "fw1", "vdom": "root"}]),
                CLITemplate(name="pt_unused_defined"),
                CLITemplate(name="to_delete_pre_run"),
            ],
            templates=[
                CLITemplate(name="used", scope_member=[{"name": "group1"}]),
                CLITemplate(name="in_template_group"),
                CLITemplate(name="t_in_deleted_template_group"),
                CLITemplate(name="to_delete_template"),
                CLITemplate(name="t_defined"),
            ],
            template_groups=[
                CLITemplateGroup(name="used", member=["in_template_group"], scope_member=[{"name": "group2"}]),
                CLITemplateGroup(name="g_in_deleted_template_group"),
                CLITemplateGroup(
                    name="to_delete_group", member=["t_in_deleted_template_group", "g_in_deleted_template_group"]
                ),
                CLITemplateGroup(name="g_defined"),
            ],
        )
        repo_tree = TemplateTree(
            pre_run_templates=[
                CLITemplate(name="pt_unused_defined"),
            ],
            templates=[
                CLITemplate(name="t_defined"),
            ],
            template_groups=[
                CLITemplateGroup(name="g_defined"),
            ],
        )
        to_delete_tree = FMGSyncTask._find_unused_templates(repo_tree=repo_tree, fmg_tree=fmg_tree)
        # check that only valid object would be deleted
        assert all(
            [
                template in to_delete_tree.pre_run_templates
                for template in [
                    "to_delete_pre_run",
                ]
            ]
        )

        assert all(
            [
                template in to_delete_tree.templates
                for template in [
                    "t_in_deleted_template_group",
                    "to_delete_template",
                ]
            ]
        )

        assert all(
            [
                group in to_delete_tree.template_groups
                for group in [
                    "to_delete_group",
                    "g_in_deleted_template_group",
                ]
            ]
        )

    def test_sanitize_good_vars(self):
        """Test sanitize_variables with same default values"""
        variables = [
            Variable(name="var1"),
            Variable(name="var2"),
            Variable(name="var3"),
            Variable(name="var1", description="Ignored description"),
        ]
        assert len(sanitize_variables(variables)) == 3

    def test_sanitize_conflicting_vars(self):
        """Test sanitize_variables with different default values"""
        variables = [
            Variable(name="var1", value="1"),
            Variable(name="var2"),
            Variable(name="var3"),
            Variable(name="var1", value="2", description="Ignored description"),
        ]
        with pytest.raises(FMGSyncVariableException):
            sanitize_variables(variables)

    def test_template_tree_variables(self):
        tree = TemplateTree(
            template_groups=[CLITemplateGroup(name="group1", variables=[Variable(name="var1")])],
            pre_run_templates=[CLITemplate(name="pre-run-template1", variables=[Variable(name="var2")])],
            templates=[CLITemplate(name="template1", variables=[Variable(name="var2")])],
        )
        assert all([var in tree.variables for var in [Variable(name="var1"), Variable(name="var2")]])
