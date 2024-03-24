"""Miscellaneous utilities."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, List

from jinja2 import Environment, meta
from more_itertools import first
from ruamel.yaml import YAML

from fortimanager_template_sync.exceptions import FMGSyncVariableException

if TYPE_CHECKING:
    from fortimanager_template_sync.fmg_api.data import Variable

logger = logging.getLogger(__name__)

yaml = YAML(typ="safe", pure=True)
# --8<-- [start:default_logging]
DEFAULT_LOGGING = yaml.load(
    """\
---
version: 1
formatters:
  simple_format:
    format: "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s"
    datefmt: "[%Y-%m-%d %H:%M:%S]"

handlers:
  console:
    class : logging.StreamHandler
    formatter: simple_format
    level   : DEBUG

loggers:
  fortimanager_template_sync:
    level: INFO

root:
  level: WARNING
  handlers: [console]
"""
)
# --8<-- [end:default_logging]


def get_logging_config(config: str):
    """prepare logging config and convert it to dict"""
    if config is None:
        return DEFAULT_LOGGING
    if Path(config).is_file():
        with open(config, encoding="UTF-8") as fi:
            config = yaml.load(fi)
        return config
    raise ValueError(f"File '{config}' not found!")


def find_all_vars(template_content: str) -> set:
    """
    Find all undeclared variables in the given template content.

    Args:
        template_content (str): The content of the template.

    Returns:
        list: A list of undeclared variables found in the template content.
    """
    env = Environment()
    parsed_content = env.parse(template_content)

    return meta.find_undeclared_variables(parsed_content)


def sanitize_variables(variables: List["Variable"]) -> List["Variable"]:
    """De-dup and check variables, so they are unique in name and default value

    Args:
        variables: input list of variables

    Returns:
        list of variables

    Raises:
        FMGSyncVariableException: on variable definition problem
    """
    good_variables = []
    for variable in variables:
        if variable.name not in good_variables:
            good_variables.append(variable)
            continue
        existing_var = first([var for var in good_variables if var.name == variable.name])
        if variable.value != existing_var.value:
            error = f"Variable {variable.name} has multiple default values amongst templates!"
            logger.error(error)
            raise FMGSyncVariableException(error)

    return good_variables
