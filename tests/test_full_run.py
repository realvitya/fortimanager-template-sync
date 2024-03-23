"""Test FMG API features"""
import os

import pytest

from typer.testing import CliRunner
from fortimanager_template_sync.__main__ import app

need_lab = pytest.mark.skipif(not pytest.lab_config, reason=f"Lab config {pytest.lab_config_file} does not exist!")
runner = CliRunner()


@need_lab
@pytest.mark.skipif(not os.getenv("TEST_INTEGRATION"), reason="TEST_INTEGRATION environment variable is not set")
class TestFullLabRun:
    """Lab tests"""

    def test_full_sync_dry_task_run(self):
        result = runner.invoke(app, ["-DD", "sync"])
        assert result.exit_code == 0

    def test_full_sync_task_run(self):
        result = runner.invoke(app, ["-DD", "sync", "-f"])
        assert result.exit_code == 0

    def test_full_deploy_dry_task_run(self):
        result = runner.invoke(app, ["-DD", "deploy"])
        assert result.exit_code == 0

    def test_full_deploy_task_run(self):
        result = runner.invoke(app, ["-DD", "deploy", "-f"])
        assert result.exit_code == 0
