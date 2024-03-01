"""Test GIT features"""

import os
import shutil
import stat
import textwrap
from pathlib import Path
from typing import Callable, Tuple

import pytest
from git import Repo

from fortimanager_template_sync.fmg_api.data import CLITemplate, Variable
from fortimanager_template_sync.sync_task import FMGSyncTask

need_lab = pytest.mark.skipif(not pytest.lab_config, reason=f"Lab config {pytest.lab_config_file} does not exist!")
use_remote_git = pytest.mark.skipif(not pytest.lab_config.git_token, reason="Not remote git token specified!")


def on_rm_error(func: Callable, path: str, exc_info: Tuple) -> None:
    """
    Removes the specified file, assuming it's read-only and unlinks it.

    Parameters:
        func (Callable): The function to be executed.
        path (str): The path of the file that couldn't be removed.
        exc_info (Tuple): Information about the exception that occurred.

    Returns:
        None

    Note:
        - The method assumes that the specified file is read-only.
        - The method unlinks the file using the specified path.
    """
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)


@need_lab
class TestGit:
    """Test GIT features"""

    task = FMGSyncTask(settings=pytest.lab_config)

    @use_remote_git
    def test_update_local_repository_clone(self):
        """Test cloning to local repository"""
        # Clear local repository first
        shutil.rmtree(self.task.settings.local_repo, ignore_errors=False, onerror=on_rm_error)
        # Re-create repo folder
        os.makedirs(self.task.settings.local_repo)
        repo = self.task._update_local_repository()
        assert isinstance(repo, Repo)
        assert Path(repo.working_dir) == self.task.settings.local_repo.absolute()

    @use_remote_git
    def test_update_local_repository_update(self):
        """Test update local repository"""
        repo = self.task._update_local_repository()
        assert isinstance(repo, Repo)
        assert Path(repo.working_dir) == self.task.settings.local_repo.absolute()

    def test_parse_template_data(self):
        """Test parse template file"""
        name = "test_template"
        data = textwrap.dedent(
            """\
            {# Initial setup for FG100F for firewall
            updated: 2023.02.14.
            1. Remove port1-20 from lan switch
            2. clears DHCP server configuration
            3. setup mgmt interface
            4. adds default route for mgmt interface

            #Used vars:
            mgmt_interface  : Management interface name (default: mgmt)
            mgmt_ip         : mgmt interface ip/nm (e.g. 1.1.1.1/24)
            mgmt_gateway    : mgmt interface default gw (e.g 1.1.1.2)
            #Assigned to: {"name": "group1"}
            -#}
            {# j2lint: disable=jinja-statements-delimiter #}
            {{ mgmt_interface }}
            {% if mgmt_ip %}
                {{ mgmt_gateway }}
            {% endif %}
            {{ DVMDB.interfaces }}
            {{ undocumented_var }}
            """
        )
        template = self.task._parse_template_data(name=name, data=data)
        # test string comparison
        assert "mgmt_interface" in template.variables
        # test object comparison
        assert Variable(name="mgmt_ip", description="mgmt interface ip/nm (e.g. 1.1.1.1/24)") in template.variables
        assert template.scope_member[0].get("name")

    def test_parse_template_group_data(self):
        """Test parsing of template-group"""
        name = "test_template_group"
        data = textwrap.dedent(
            """\
            {# Test template group
            # assigned to: {"name": "test_group"}
            -#}
            {# j2lint: disable=jinja-statements-delimiter #}
            {% include "templates/template1.j2" %}

            {% include "templates/template2.j2" %}
            """
        )
        template1 = CLITemplate(name="template1", variables=[Variable(name="var1"), Variable(name="var2")])
        template2 = CLITemplate(name="template2", variables=[Variable(name="var3"), Variable(name="var4")])
        templates = [template1, template2]
        template_group = self.task._parse_template_groups_data(name=name, data=data, templates=templates)
        assert (
            all([var in template_group.variables for var in ["var1", "var2", "var3", "var4"]])
            and template_group.description == "Test template group"
            and template_group.member == ["template1", "template2"]
        )
        assert template_group.scope_member[0].get("name") == "test_group"

    def test_load_local_repository(self):
        """Test load local repository"""
        templates = self.task._load_local_repository()
        # only check if we read something. Useful to test custom test repositories
        assert templates.templates
        assert templates.pre_run_templates
        assert templates.template_groups[0].member
