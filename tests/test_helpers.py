"""Test helper functions/methods"""
import pytest

from fortimanager_template_sync.exceptions import FMGSyncInvalidStatusException
from fortimanager_template_sync.task import FMGSyncTask


class TestHelpers:
    """Test helper functions"""

    def test_ensure_device_statuses_good(self):
        statuses = {
            "good_fw": {
                "conf_status": "insync",
                "db_status": "nomod",
                "dev_status": "auto_updated"
            },
            "good_fw2": {
                "conf_status": "insync",
                "db_status": "nomod",
                "dev_status": "unknown"
            }
        }

        FMGSyncTask._ensure_device_statuses(statuses)

    def test_ensure_device_statuses_problem(self):
        statuses = {
            "good_fw": {
                "conf_status": "insync",
                "db_status": "nomod",
                "dev_status": "auto_updated"
            },
            "problematic_fw": {
                "conf_status": "outofsync",
                "db_status": "mod",
                "dev_status": "timeout"
            }
        }

        with pytest.raises(FMGSyncInvalidStatusException, match=r"problematic_fw"):
            FMGSyncTask._ensure_device_statuses(statuses)
