"""Test GIT features"""
import os
import shutil
import textwrap

import pytest
from git import Repo

from fortimanager_template_sync.fmg_api.data import Variable
from fortimanager_template_sync.task import FMGSyncTask

need_lab = pytest.mark.skipif(not pytest.lab_config, reason=f"Lab config {pytest.lab_config_file} does not exist!")
use_remote_git = pytest.mark.skipif(not pytest.lab_config.git_token, reason=f"Not remote git token specified!")


@need_lab
class TestGit:
    """Test GIT features"""

    task = FMGSyncTask(settings=pytest.lab_config)

    @use_remote_git
    def test_update_local_repository_clone(self):
        """Test update local repository"""
        # Clear local repository first
        shutil.rmtree(self.task.settings.local_repo, ignore_errors=True)
        # Re-create repo folder
        os.makedirs(self.task.settings.local_repo)
        repo = self.task._update_local_repository()
        assert isinstance(repo, Repo)
        assert repo.working_dir == self.task.settings.local_repo

    @use_remote_git
    def test_update_local_repository_update(self):
        """Test update local repository"""
        repo = self.task._update_local_repository()
        assert isinstance(repo, Repo)
        assert repo.working_dir == self.task.settings.local_repo

    def test_parse_template_file(self):
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
    
            Used vars:
            mgmt_interface  : Management interface name (default: mgmt)
            mgmt_ip         : mgmt interface ip/nm (e.g. 1.1.1.1/24)
            mgmt_gateway    : mgmt interface default gw (e.g 1.1.1.2)
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
        template = self.task._parse_template_file(name=name, data=data)
        # test string comparison
        assert "mgmt_interface" in template.variables
        # test object comparison
        assert Variable(name="mgmt_ip", description="mgmt interface ip/nm (e.g. 1.1.1.1/24)") in template.variables

    def test_load_local_repository(self):
        """Test load local repository"""
