"""Fortimanager settings"""
from pydantic import Field, SecretStr, field_validator
from pydantic.networks import HttpUrl
from pydantic_settings import BaseSettings


class FMGSettings(BaseSettings):
    """Fortimanager settings"""

    base_url: HttpUrl = Field(..., description="Base URL to access FMG (e.g.: https://myfmg/jsonrpc)")
    username: str = Field(..., description="User to authenticate")
    password: SecretStr = Field(..., description="Password for authentication")
    adom: str = Field("Global", description="ADOM to use for this connection")
    verify: bool = Field(True, description="Verify SSL certificate (REQUESTS_CA_BUNDLE can set accepted CA cert)")

    @field_validator("base_url", mode="before")
    @classmethod
    def check_base_url(cls, v: str):  # pylint: disable=invalid-name
        """check and fix base_url"""
        v = v.rstrip("/ ")
        if not v.endswith("/jsonrpc"):
            v += "/jsonrpc"
        return HttpUrl(v)
