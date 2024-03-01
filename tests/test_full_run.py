"""Test FMG API features"""
import pytest
from fortimanager_template_sync.__main__ import app

need_lab = pytest.mark.skipif(not pytest.lab_config, reason=f"Lab config {pytest.lab_config_file} does not exist!")


@need_lab
@pytest.mark.skip()
class TestFullLabRun:
    """Lab tests"""

    def test_full_sync_task_run(self):
        app("-DD", "sync")

    def test_full_deploy_task_run(self):
        app("-DD", "deploy")
