"""FW deployment task"""
import logging
from typing import Optional

from fortimanager_template_sync.config import FMGSyncSettings
from fortimanager_template_sync.fmg_api import FMGSync

logger = logging.getLogger("fortimanager_template_sync.deploy_task")


class FMGDeployTask:
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
