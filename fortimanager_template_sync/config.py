"""Configuration model"""
from pathlib import Path
from typing import Optional, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from ruamel import yaml

DEFAULT_LOGGING = yaml.safe_load(
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


class FMGSyncSettings(BaseSettings):
    """Application settings"""

    debug: int = 0
    logging_config: Optional[Union[str, dict]]
    prod_run: bool

    model_config = SettingsConfigDict(
        env_file=".env", env_nested_delimiter="__", extra="ignore", case_sensitive=True, hide_input_in_errors=True
    )

    @classmethod
    @field_validator("logging_config")
    def check_logging_config(cls, config):
        """prepare logging config and convert it to dict"""
        if config is None:
            return DEFAULT_LOGGING
        if Path(config).is_file():
            with open(config, encoding="UTF-8") as fi:
                config = yaml.safe_load(fi)
            return config
        raise ValueError(f"File '{config}' not found!")
