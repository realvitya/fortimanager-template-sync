"""Main program"""

import logging
from logging.config import dictConfig
from typing import Annotated, Optional

import dotenv
import typer

from fortimanager_template_sync import __version__
from fortimanager_template_sync.deploy_run import deploy_run
from fortimanager_template_sync.misc import get_logging_config
from fortimanager_template_sync.sync_run import sync_run

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, add_completion=False, no_args_is_help=True)
app.command(name="sync", help="GIT/FMG sync operation")(sync_run)
app.command(name="deploy", help="Firewall deployment operation")(deploy_run)

logger = logging.getLogger("fortimanager_template_sync.main")


@app.callback(invoke_without_command=True, no_args_is_help=True)
def main(
    version: Annotated[bool, typer.Option("--version", "-V", help="print version")] = False,
    logging_config: Annotated[
        Optional[str], typer.Option("--logging_config", "-l", help="logging config file in YAML format")
    ] = None,
    debug: Annotated[int, typer.Option("--debug", "-D", help="debug logs", count=True)] = 0,
):
    """Fortimanager Template Sync"""
    # This function runs before each task (sync/deploy)
    if version:
        print(f"Fortimanager Template Sync version: {__version__}")
        return

    # setup logging
    dictConfig(get_logging_config(logging_config))
    if not debug:
        app.pretty_exceptions_show_locals = False  # disable debug info in exceptions (security)
    if debug > 0:
        logging.getLogger("fortimanager_template_sync").setLevel(logging.DEBUG)
    if debug > 1:
        app.pretty_exceptions_show_locals = True
    if debug > 2:
        logging.level = logging.DEBUG

    # load environment variables for tests
    # in production this should not have an effect as variables must be provided by the OS
    dotenv.load_dotenv("fmgsync.env")


if __name__ == "__main__":
    app()
