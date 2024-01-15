"""Pydantic data types"""
from typing import List, Literal

from pydantic import BaseModel, field_validator


class CLITemplate(BaseModel):
    name: str
    description: str = ""
    provision: Literal["disable", "enable"] = "disable"
    script: str = ""
    type: Literal["cli", "jinja"] = "jinja"
    variables: List[str] = None

    @field_validator("provision", mode="before")
    def standardize_provision(cls, v):
        """Convert int to string"""
        if type(v) is int:
            return ["disable", "enable"][v]
        else:
            return v

    @field_validator("type", mode="before")
    def standardize_type(cls, v):
        """Convert int to string"""
        if type(v) is int:
            return ["cli", "jinja"][v]
        else:
            return v


class CLITemplateGroup(BaseModel):
    name: str
    description: str = ""
    member: List[str] = None
    variables: List[str] = None
