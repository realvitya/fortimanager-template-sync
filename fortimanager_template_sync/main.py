"""Main program"""
import logging
import time
from logging.config import dictConfig

import typer
from typing_extensions import Annotated

from fortimanager_template_sync import __version__
from fortimanager_template_sync.config import FMGSyncSettings

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, add_completion=False)
logger = logging.getLogger("fortimanager_template_sync.main")


@app.command()
def run(
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
    print(settings)
    logger.info("Operation took %ss", round(time.time() - start_time, 2))


def main():
    """Typer runner"""
    app()


if __name__ == "__main__":
    main()
