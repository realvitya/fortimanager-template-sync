"""Miscellaneous utilities."""
from pathlib import Path

from jinja2 import Environment, meta
from ruamel.yaml import YAML

yaml = YAML(typ="safe", pure=True)
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
