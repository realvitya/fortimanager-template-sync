"""FW deployment task"""
import logging
from typing import Optional

from fortimanager_template_sync.common_task import CommonTask
from fortimanager_template_sync.config import FMGSyncSettings
from fortimanager_template_sync.fmg_api import FMGSync

logger = logging.getLogger("fortimanager_template_sync.deploy_task")


class FMGDeployTask(CommonTask):
    """
        Fortimanager Deployment Task

    Steps of this task:

        1. check firewall statuses
        2. deploy changes to firewalls in protected group only
        3. check firewall statuses again

    Attributes:
        settings (FMGSyncSettings): task settings to use
        fmg (FMGSync): FMG instance
    """

    def run(self):
        """Run task

        Raises:
            FMGSyncVariableException: on invalid variable definitions or conflict
            FMGSyncInvalidStatusException: on invalid device status
        """
        success = True
        try:
            self.fmg = FMGSync(
                        base_url=self.settings.fmg_url,
                        username=self.settings.fmg_user,
                        password=self.settings.fmg_pass,
                        adom=self.settings.fmg_adom,
                        verify=self.settings.fmg_verify,
                    )
        # 1. check firewall statuses
            statuses = self._get_firewall_statuses(self.settings.protected_fw_group)

        # 2. deploy changes to firewalls in protected group only
        # 3. check firewall statuses again
        finally:
            self.fmg.close(discard_changes=not success)