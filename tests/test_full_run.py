"""Test FMG API features"""
import pytest
from pyfortinet.exceptions import FMGUnhandledException
from pyfortinet.fmg_api.common import F

from fortimanager_template_sync.fmg_api.connection import FMGSync
from fortimanager_template_sync.fmg_api.data import CLITemplate, CLITemplateGroup
from fortimanager_template_sync.sync_task import FMGSyncTask

need_lab = pytest.mark.skipif(not pytest.lab_config, reason=f"Lab config {pytest.lab_config_file} does not exist!")


@need_lab
class TestFullLabRun:
    """Lab tests"""

    fmg = FMGSync(
        base_url=pytest.lab_config.fmg_url,
        username=pytest.lab_config.fmg_user,
        password=pytest.lab_config.fmg_pass,
        adom=pytest.lab_config.fmg_adom,
        verify=False,
    ).open()
    fmg_connected = pytest.mark.skipif(
        not fmg._token,
        reason=f"FMG {pytest.lab_config.fmg_url} is not connected!",
    )
    task = FMGSyncTask(settings=pytest.lab_config, fmg=fmg)

    @fmg_connected
    def test_full_task_run(self):
        self.task.run()
