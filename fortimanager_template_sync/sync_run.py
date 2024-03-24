import logging
import time
from pathlib import Path
from typing import Annotated

import typer
import urllib3

from fortimanager_template_sync.config import FMGSyncSettings
from fortimanager_template_sync.sync_task import FMGSyncTask

logger = logging.getLogger("fortimanager_template_sync.sync_run")


def sync_run(
    template_repo: Annotated[
        str, typer.Option("--template-repo", "-t", envvar="FMGSYNC_TEMPLATE_REPO", help="Template repository URL")
    ] = None,
    template_branch: Annotated[
        str,
        typer.Option("--template-branch", "-b", envvar="FMGSYNC_TEMPLATE_BRANCH", help="Branch in repository to sync"),
    ] = "main",
    git_token: Annotated[str, typer.Option("--git-token", envvar="FMGSYNC_GIT_TOKEN")] = None,
    local_repo: Annotated[Path, typer.Option("--local-path", "-l", envvar="FMGSYNC_LOCAL_REPO")] = "./fmg-templates/",
    fmg_url: Annotated[str, typer.Option("--fmg-url", "-url", envvar="FMGSYNC_FMG_URL")] = None,
    fmg_user: Annotated[str, typer.Option("--fmg-user", "-u", envvar="FMGSYNC_FMG_USER")] = None,
    fmg_pass: Annotated[str, typer.Option("--fmg-pass", "-p", envvar="FMGSYNC_FMG_PASS")] = None,
    fmg_adom: Annotated[str, typer.Option("--fmg-adom", "-a", envvar="FMGSYNC_FMG_ADOM")] = "root",
    fmg_verify: Annotated[bool, typer.Option(envvar="FMGSYNC_FMG_VERIFY")] = True,
    protected_fw_group: Annotated[
        str,
        typer.Option(
            "--protected-firewall-group",
            "-pg",
            envvar="FMGSYNC_PROTECTED_FW_GROUP",
            help="This group in FMG will be checked for FW status. Also this group will be deployed only",
        ),
    ] = "automation",
    delete_unused_templates: Annotated[bool, typer.Option("--delete-unused-templates", "-d")] = False,
    prod_run: Annotated[bool, typer.Option("--force-changes", "-f", help="do changes")] = False,
):
    """GIT/FMG sync operation"""

    settings = FMGSyncSettings(
        template_repo=template_repo,
        template_branch=template_branch,
        git_token=git_token,
        local_repo=local_repo,
        fmg_url=fmg_url,
        fmg_user=fmg_user,
        fmg_pass=fmg_pass,
        fmg_adom=fmg_adom,
        fmg_verify=fmg_verify,
        protected_fw_group=protected_fw_group,
        delete_unused_templates=delete_unused_templates,
        prod_run=prod_run,
    )
    if not fmg_verify:
        urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)
    start_time = time.time()
    result = False
    try:
        task = FMGSyncTask(settings)
        result = task.run()
    except Exception as err:
        logger.error(err)
    finally:
        logger.info("Operation took %ss", round(time.time() - start_time, 2))
        if result:
            logger.info("Sync task finished successfully!")
            exit(0)
        else:
            logger.warning("Sync task finished with problems!")
            exit(1)
