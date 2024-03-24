"""Configuration model"""
from pathlib import Path
from typing import Optional

from pydantic import AnyHttpUrl, SecretStr, field_validator
from pydantic_core import Url
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class FMGSyncSettings(BaseSettings):
    """Application settings"""

    git_token: Optional[SecretStr] = None
    template_repo: str
    template_branch: str
    local_repo: Path
    fmg_url: str
    fmg_user: str
    fmg_pass: SecretStr
    fmg_adom: str
    fmg_verify: bool = True
    protected_fw_group: str
    delete_unused_templates: bool = False
    prod_run: bool = False

    model_config = SettingsConfigDict(
        env_file="fmgsync.env",
        env_nested_delimiter="__",
        env_prefix="FMGSYNC_",
        extra="ignore",
        case_sensitive=False,
        hide_input_in_errors=True,
    )

    @field_validator("template_repo", mode="after")
    def update_token_in_repo_url(cls, v: str, info: ValidationInfo):
        """add token to url if needed"""
        url = AnyHttpUrl(v)
        git_token: SecretStr = info.data.get("git_token")  # type: ignore # calm mypy, type is assured by pydantic
        if not git_token:
            return v
        url_with_token = Url.build(
            scheme=url.scheme, username=git_token.get_secret_value(), host=url.host or "", port=url.port, path=url.path
        )
        return str(url_with_token)

    @field_validator("fmg_url", mode="after")
    def validate_fmg_url(cls, url: str):
        """convert value to string"""
        assert AnyHttpUrl(url)
        return url

    @field_validator("local_repo")
    def validate_local_repo(cls, path: Path):
        """ensure local repo exists"""
        path.mkdir(exist_ok=True)
        return path
