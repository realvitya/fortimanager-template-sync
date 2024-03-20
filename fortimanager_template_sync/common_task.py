import logging
from typing import Any, Dict, Optional

from pyfortinet.fmg_api.common import F, FilterList

from fortimanager_template_sync.config import FMGSyncSettings
from fortimanager_template_sync.exceptions import FMGSyncInvalidStatusException
from fortimanager_template_sync.fmg_api import FMGSync

logger = logging.getLogger(__name__)


DEV_STATUS = {
    0: "none",
    "none": "none",
    1: "unknown",
    "unknown": "unknown",
    2: "checkedin",
    "checkedin": "checkedin",
    3: "inprogress",
    "inprogress": "inprogress",
    4: "installed",
    "installed": "installed",
    5: "aborted",
    "aborted": "aborted",
    6: "sched",
    "sched": "sched",
    7: "retry",
    "retry": "retry",
    8: "canceled",
    "canceled": "canceled",
    9: "pending",
    "pending": "pending",
    10: "retrieved",
    "retrieved": "retrieved",
    11: "changed_conf",
    "changed_conf": "changed_conf",
    12: "sync_fail",
    "sync_fail": "sync_fail",
    13: "timeout",
    "timeout": "timeout",
    14: "rev_revert",
    "rev_revert": "rev_revert",
    15: "auto_updated",
    "auto_updated": "auto_updated",
}

DB_STATUS = {
    0: "unknown",
    "unknown": "unknown",
    1: "nomod",
    "nomod": "nomod",
    2: "mod",
    "mod": "mod",
}

CONF_STATUS = {
    0: "unknown",
    "unknown": "unknown",
    1: "insync",
    "insync": "insync",
    2: "outofsync",
    "outofsync": "outofsync",
}


class CommonTask:
    """Common task functionalities"""

    def __init__(self, settings: FMGSyncSettings, fmg: Optional[FMGSync] = None):
        """Initialize task

        Args:
            settings: task settings
            fmg: FMG connection if there is any
        """
        self.settings = settings
        self.fmg = fmg

    def _get_firewall_statuses(self, group: str) -> Dict[str, Dict[str, Any]]:
        """Gather firewall statuses in the specified group"""
        logger.info("Gathering firewall statuses in group '%s'", group)
        statuses = {}
        device_list = self.fmg.get_group_members(group_name=group)
        if "object member" not in device_list.data.get("data", {}):
            logger.debug("No devices found in group '%s'", group)
            return statuses
        filters = FilterList()
        for device in device_list.data.get("data", {}).get("object member"):
            filters += F(name=device["name"])
        logger.debug("Found %d devices", len(filters))
        device_list = self.fmg.get_devices(filters=filters)
        for device_status in device_list.data.get("data"):
            statuses[device_status["name"]] = {
                "conf_status": CONF_STATUS.get(device_status["conf_status"]),
                "db_status": DB_STATUS.get(device_status["db_status"]),
                "dev_status": DEV_STATUS.get(device_status["dev_status"]),
                "cli_status": {  # collect CLI template assignments for each VDOM
                    vdom["name"]: assign
                    for vdom in device_status.get("vdom", [])
                    for assign in vdom.get("assignment info", [])
                    if assign["type"] == "cli"
                },
            }
            logger.debug("Device %s: %s", device_status["name"], statuses[device_status["name"]])
            if any(value is None for value in statuses[device_status["name"]].values()):
                error = f"Status of {device_status['name']} is invalid: {statuses[device_status['name']]}"
                logger.error(error)
                raise FMGSyncInvalidStatusException(error)
        return statuses

    @staticmethod
    def _ensure_device_statuses(statuses: Dict):
        for device, status in statuses.items():
            if status["conf_status"] not in ("insync",) or status["db_status"] not in ("nomod",):
                error = f"Device '{device}' has problem with status: {status}"
                logger.error(error)
                raise FMGSyncInvalidStatusException(error)
