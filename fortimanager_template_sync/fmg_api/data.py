"""Pydantic data types"""
from typing import List, Literal, Optional, Dict

from pydantic import BaseModel, field_validator


class Variable(BaseModel):
    """Variable model"""

    name: str
    description: Optional[str] = None
    value: Optional[str] = None

    def __eq__(self, other):
        """Add support for string equality"""
        if isinstance(other, str):
            return self.name == other
        else:
            return super().__eq__(other)


class CLITemplate(BaseModel):
    """CLI template model

    Docs for assigning template to device
    https://fndn.fortinet.net/index.php?/stackoverflow/topic/607-cli-template/&tab=comments#comment-2602
    """

    name: str
    description: str = ""
    provision: Literal["disable", "enable"] = "disable"
    script: str = ""
    type: Literal["cli", "jinja"] = "jinja"
    variables: Optional[List[Variable]] = None
    scope_member: Optional[List[Dict[str, str]]] = None  # list of object this is assigned to

    def __eq__(self, other):
        """Add support for string equality"""
        if isinstance(other, str):
            return self.name == other
        else:
            return super().__eq__(other)

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
    """CLI Template Group model"""

    name: str
    description: str = ""
    member: Optional[List[str]] = None  # list of templates and template-groups (yes, their name is unique)
    variables: Optional[List[Variable]] = None
    scope_member: Optional[List[Dict[str, str]]] = None  # list of object this is assigned to

    def __eq__(self, other):
        """Add support for string equality"""
        if isinstance(other, str):
            return self.name == other
        else:
            return super().__eq__(other)
