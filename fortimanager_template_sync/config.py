"""Configuration model"""
from pathlib import Path
from typing import Optional, Union

from pydantic import field_validator, SecretStr, AnyHttpUrl, DirectoryPath
from pydantic_core import Url
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
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


class FMGSyncSettings(BaseSettings):
    """Application settings"""

    git_token: Optional[SecretStr] = None
    template_repo: AnyHttpUrl
    template_branch: str
    local_repo: DirectoryPath
    fmg_url: AnyHttpUrl
    fmg_user: str
    fmg_pass: SecretStr
    fmg_adom: str
    fmg_verify: bool = True
    protected_fw_group: str
    debug: int = 0
    logging_config: Optional[Union[str, dict]] = None
    prod_run: bool = False

    model_config = SettingsConfigDict(
        env_file="fmgsync.env",
        env_nested_delimiter="__",
        env_prefix="FMGSYNC_",
        extra="ignore",
        case_sensitive=False,
        hide_input_in_errors=True,
    )

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

    @field_validator("template_repo", mode="after")
    def update_token_in_repo_url(cls, url: AnyHttpUrl, info: ValidationInfo):
        git_token: SecretStr = info.data.get("git_token")  # type: ignore # calm mypy, type is assured by pydantic
        if not git_token:
            return str(url)
        url_with_token = Url.build(
            scheme=url.scheme, username=git_token.get_secret_value(), host=url.host or "", port=url.port, path=url.path
        )
        return str(url_with_token)

    @field_validator("fmg_url", mode="after")
    def validate_fmg_url(cls, url: AnyHttpUrl, info: ValidationInfo):
        return str(url)
