"""Main program"""
import logging
import time
from logging.config import dictConfig
from pathlib import Path

import dotenv
import typer
from typing_extensions import Annotated

from fortimanager_template_sync import __version__
from fortimanager_template_sync.config import FMGSyncSettings
from fortimanager_template_sync.task import FMGSyncTask

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, add_completion=False)
logger = logging.getLogger("fortimanager_template_sync.main")


@app.command()
def run(
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
    fmg_verify: Annotated[bool, typer.Option("--fmg-verify", "-vf", envvar="FMGSYNC_FMG_VERIFY")] = True,
    protected_fw_group: Annotated[
        str,
        typer.Option(
            "--protected-firewall-group",
            "-pg",
            envvar="FMGSYNC_PROTECTED_FW_GROUP",
            help="This group in FMG will be checked for FW status. Also this group will be deployed only",
        ),
    ] = "production",
    version: Annotated[bool, typer.Option("--version", "-V", help="print version")] = False,
    prod_run: Annotated[bool, typer.Option("--force-changes", "-f", help="do changes")] = False,
    debug: Annotated[int, typer.Option("--debug", "-D", help="debug logs", count=True)] = 0,
    logging_config: Annotated[
        str, typer.Option("--logging_config", "-l", help="logging config file in YAML format")
    ] = None,
):
    """Main program"""
    if version:
        print(f"Fortimanager Template Sync version: {__version__}")
        return

    settings = FMGSyncSettings(
        template_repo=template_repo,
        template_branch=template_branch,
        git_token=git_token,
        local_repo=local_repo,
        fmg_url=fmg_url,
        fmg_user=fmg_user,
        fmg_pass=fmg_pass,
        fmg_adom=fmg_adom,
        fmg_adom_password=fmg_verify,
        protected_fw_group=protected_fw_group,
        prod_run=prod_run,
        debug=debug,
        logging_config=logging_config,
    )

    # setup logging
    dictConfig(settings.logging_config)
    if settings.debug > 0:
        logging.getLogger("fortimanager_template_sync").setLevel(logging.DEBUG)
    if settings.debug > 1:
        logging.level = logging.DEBUG

    start_time = time.time()
    job = FMGSyncTask(settings)
    job.run()
    logger.info("Operation took %ss", round(time.time() - start_time, 2))


def main():
    """Typer runner"""
    dotenv.load_dotenv("fmgsync.env")
    app()


if __name__ == "__main__":
    main()
