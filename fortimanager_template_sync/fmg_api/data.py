"""Pydantic data types"""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic.dataclasses import dataclass

from fortimanager_template_sync.misc import sanitize_variables


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
    # return value only on loadsub
    scope_member: Optional[List[Dict[str, str]]] = Field(None, exclude=True)  # list of object this is assigned to

    def __eq__(self, other):
        """Add support for string equality"""
        if isinstance(other, str):
            return self.name == other
        elif isinstance(other, CLITemplate):
            # return super().__eq__(other)  # not working, variables can differ being list of other objects
            svars = sorted([var.name for var in self.variables]) if self.variables else self.variables
            ovars = sorted([var.name for var in other.variables]) if other.variables else other.variables
            sscope = sorted([scope for scope in self.scope_member]) if self.scope_member else self.scope_member
            oscope = sorted([scope for scope in other.scope_member]) if other.scope_member else other.scope_member
            return (
                self.name == other.name
                and self.description == other.description
                and self.provision == other.provision
                and self.script == other.script
                and self.type == other.type
                and svars == ovars
                and sscope == oscope
            )
        else:  # e.g. None
            return False

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
    # return value only on loadsub
    scope_member: Optional[List[Dict[str, str]]] = Field(None, exclude=True)  # list of object this is assigned to

    def __eq__(self, other):
        """Add support for string equality"""
        if isinstance(other, str):
            return self.name == other
        elif isinstance(other, CLITemplateGroup):
            # return super().__eq__(other)  # not working, variables can differ being list of other objects
            if not self.name == other.name:
                return False
            if not self.description == other.description:
                return False
            if not isinstance(self.member, list):
                if not self.member == other.member:
                    return False
            elif not sorted(self.member) == sorted(other.member):
                return False
            if not isinstance(self.variables, list):
                if not self.variables == other.variables:
                    return False
            elif not sorted([var.name for var in self.variables]) == sorted([var.name for var in other.variables]):
                return False
            if not isinstance(self.scope_member, list):
                if not self.scope_member == other.scope_member:
                    return False
            else:
                return sorted([scope for scope in self.scope_member]) == sorted([scope for scope in other.scope_member])
        else:  # e.g. None
            return False


@dataclass
class TemplateTree:
    """Template data structure

    Attributes:
        pre_run_templates (List[CLITemplate]): CLI pre-run template list
        templates (List[CLITemplate]): CLI template list
        template_groups (List[CLITemplateGroup]): CLI template group list
    """

    pre_run_templates: List[CLITemplate]
    templates: List[CLITemplate]
    template_groups: List[CLITemplateGroup]

    def __bool__(self) -> bool:
        """Check for empty tree

        Returns:
            True if there is any template or template group in the tree
        """
        return bool(len(self.pre_run_templates) + len(self.templates) + len(self.template_groups))

    @property
    def variables(self) -> List[Variable]:
        """Get list of all variables"""
        variables = [
            template.variables
            for template in self.pre_run_templates + self.templates + self.template_groups
            if template.variables
        ]
        result = []
        for variable_list in variables:
            result.extend(variable_list)
        result = sanitize_variables(result)
        return result
