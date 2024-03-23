"""FW deployment task"""

import logging
from typing import List, Dict, Any

from pyfortinet.fmg_api.common import Scope
from pyfortinet.fmg_api.securityconsole import InstallDeviceTask

from fortimanager_template_sync.common_task import CommonTask
from fortimanager_template_sync.exceptions import FMGSyncInvalidStatusException
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

    def run(self) -> bool:
        """Run deployment task

        Returns:
            (bool): True if task succeeded, False otherwise
        """
        success = True
        try:
            if not self.fmg:
                self.fmg = FMGSync(
                    base_url=self.settings.fmg_url,
                    username=self.settings.fmg_user,
                    password=self.settings.fmg_pass,
                    adom=self.settings.fmg_adom,
                    verify=self.settings.fmg_verify,
                ).open()
            # 1. check firewall statuses
            statuses = self._get_firewall_statuses(self.settings.protected_fw_group)

            # 2. find firewalls with applicable status
            to_deploy = self._get_deployable_firewalls(statuses)

            # 3. deploy changes to firewalls in protected group only
            if to_deploy:
                self._deploy_changes(to_deploy)

            # 4. check firewall statuses again
            if self.settings.prod_run and to_deploy:
                statuses = self._get_firewall_statuses(self.settings.protected_fw_group)
                to_deploy = self._get_deployable_firewalls(statuses)
                if to_deploy:
                    logger.warning("The following firewalls are still not updated: %s", list(to_deploy.keys()))
                    success = False
                else:
                    logger.info("CLI template install task ran successfully")
            else:
                logger.info("No checking required")
        finally:
            self.fmg.close()
            return success

    @staticmethod
    def _get_deployable_firewalls(statuses: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """Get list of firewall names which are to be deployed.

        Example input - statuses:
            ```python
            {
                'FW01': {
                    'cli_status': {
                        'root': {
                            'name': 'test_global', 'status': 'modified', 'type': 'cli'
                        },
                        'VDOM2': {
                            'name': 'test_global', 'status': 'modified', 'type': 'cli'
                        }
                    },
                    'conf_status': 'insync', 'db_status': 'nomod', 'dev_status': 'installed'
                },
                'FW01': {
                    'cli_status': {
                        'root': {
                            'name': 'test_global', 'status': 'modified', 'type': 'cli'
                        },
                    },
                    'conf_status': 'insync', 'db_status': 'nomod', 'dev_status': 'installed'
                }
            }
            ```

        Example output:
            ```python
            {
                "FW1": ["root", "VDOM2"],
                "FW2": ["root"],
            }
            ```

        Returns:
            List of Dicts with firewall name as key and VDOM as value

        Raises:
            (FMGSyncInvalidStatusException): In case there is a firewall with conf or db modified, error out.
        """
        to_deploy = {}
        num_of_vdoms = 0
        for fw, status in statuses.items():
            if status.get("conf_status") == "outofsync" or status.get("db_status") == "mod":
                raise FMGSyncInvalidStatusException(f"Firewall {fw} has modified configuration or database")
            modified_vdoms = [vdom for vdom in status.get("cli_status") if status["cli_status"][vdom].get("status") == "modified"]
            if modified_vdoms:
                to_deploy[fw] = modified_vdoms
                num_of_vdoms += len(to_deploy[fw])
        logger.info(f"Found {num_of_vdoms} firewall/VDOMs to deploy")
        return to_deploy

    def _deploy_changes(self, to_deploy: Dict[str, List[str]]):
        """Deploy changes to firewalls"""
        def log_install(percent, log):
            nonlocal last_log, last_percent
            if percent == last_percent and last_log == log:
                return
            last_percent = percent
            last_log = log
            logger.debug(f"{percent}%: {log}")

        last_log = ""
        last_percent = 0
        scopes = []
        for fw, vdoms in to_deploy.items():
            for vdom in vdoms:
                scopes.append(Scope(name=fw, vdom=vdom))
        if scopes:
            if not self.settings.prod_run:
                logger.info("TEST - to deploy to %s", to_deploy)
                return
            logger.debug(f"Deploying to {scopes}")
            task = self.fmg.get_obj(InstallDeviceTask, adom=self.fmg.adom, flags=["auto_lock_ws"], scope=scopes)
            result = task.exec()
            if result.success:
                logger.info(f"Running install for {len(scopes)} items")
                result.wait_for_task(timeout=len(scopes)*120,
                                     callback=log_install)
            else:
                logger.error(f"Error by installation: {result.data}")
        else:
            logger.info("No firewalls/VDOMs to install templates to")
