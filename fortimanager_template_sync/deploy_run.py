import logging
import time
from pathlib import Path
from typing import Annotated

import typer

from fortimanager_template_sync.config import FMGSyncSettings
from fortimanager_template_sync.deploy_task import FMGDeployTask


logger = logging.getLogger("fortimanager_template_sync.deploy_run")


def deploy_run(
    template_repo: Annotated[
        str, typer.Option("--template-repo", "-t", envvar="FMGSYNC_TEMPLATE_REPO", help="Template repository URL")
    ] = None,
    template_branch: Annotated[
        str,
        typer.Option("--template-branch", "-b", envvar="FMGSYNC_TEMPLATE_BRANCH", help="Branch in repository to sync"),
    ] = "main",
    git_token: Annotated[str, typer.Option("--git-token", envvar="FMGSYNC_GIT_TOKEN")] = None,
    local_repo: Annotated[Path, typer.Option("--local-path", "-l", envvar="FMGSYNC_LOCAL_PATH")] = "./fmg-templates/",
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
    ] = "production",
    delete_unused_templates: Annotated[bool, typer.Option("--delete-unused-templates", "-d")] = False,
    prod_run: Annotated[bool, typer.Option("--force-changes", "-f", help="do changes")] = False,
):
    """FMG FW deployment operation"""
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

    start_time = time.time()
    job = FMGDeployTask(settings)
    job.run()
    logger.info("Operation took %ss", round(time.time() - start_time, 2))
