"""FMG Sync Task"""
from fortimanager_template_sync.config import FMGSyncSettings


class FMGSyncTask:
    """
    Fortimanager Sync Task

    Steps of this task:
    1. update local repository from remote
    2. check if there was a change
    3. check FMG device status list
       If firewalls are not in sync, stop
    4. download FMG templates and template groups from FMG
    5. build list of templates to delete from FMG
    6. build list of templates to upload to FMG
    7. execute changes in FMG
    8. check firewall statuses
    9. deploy changes to firewalls
    10. check firewall statuses again

    Attributes:
        settings (FMGSyncSettings): task settings to use
    """

    def __init__(self, settings: FMGSyncSettings):
        """Initialize task

        Args:
            settings: task settings
        """
        self.settings = settings

    def run(self):
        """Run task

        Raises:
            FMGSyncException
        """
