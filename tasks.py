"""Invoke task file"""
import shutil
from pathlib import Path
from typing import Literal

from invoke import task


@task
def clean_dist(cmd):  # pylint: disable=unused-argument  # mandatory argument
    """Clean dist directory"""
    directory = Path("dist")
    if directory.is_dir():
        for item in directory.glob("*"):
            if item.is_dir():
                shutil.rmtree(item)
            elif item.is_file():
                item.unlink()
            print(f"{item} deleted")


@task(clean_dist)
def clean(cmd):  # pylint: disable=unused-argument  # mandatory argument
    """Clean packaging related stuff"""


@task(clean)
def build(cmd):
    """Build package"""
    cmd.run("flit build")


@task(
    help={
        "all_docs": "Process all documents instead of the changed ones",
    }
)
def mkdocs(cmd, all_docs=False):  # pylint: disable=unused-argument  # until Sphinx implemented
    """Compile docs"""
    opts = []
    if all_docs:
        opts.append("-a")
    # cmd.run("sphinx-build nautobot_scrapli_backup/docs-source docs " + " ".join(opts))
    print("mkdocs is not yet implemented!")  # TODO: create Sphinx docs


LinterType = Literal[
    "all",
    "trailing-whitespace",
    "end-of-file-fixer",
    "check-yaml",
    "check-toml",
    "black",
    "detect-secrets",
    "isort",
    "rstcheck",
    "pylint",
    "relint",
]


@task(
    help={
        "test": f"Linters to run {LinterType.__args__}",
        "all_files": "Specify to check all files instead of the stage area",
    }
)
def lint(cmd, test="all", all_files=False):
    """Run linters"""
    if "all" in test:
        cmd.run(f"pre-commit run{' --all-files' if all_files else '' }")
    else:
        cmd.run(f"pre-commit run{' --all-files' if all_files else '' } {test}")
