"""FMG connection"""

import logging
from typing import Dict, List, Literal, Optional, Union

from pyfortinet import FMG, FMGResponse
from pyfortinet.exceptions import FMGEmptyResultException
from pyfortinet.fmg_api.common import FILTER_TYPE

logger = logging.getLogger(__name__)


class FMGSync(FMG):
    """Fortimanager connection class"""

    # CLI Template operations

    def add_cli_template(
        self,
        name: str,
        script: str,
        description: str = "",
        provision: Literal["disable", "enable"] = "disable",
        type: Literal["cli", "jinja"] = "jinja",
        variables: Optional[List[dict]] = None,
    ) -> FMGResponse:
        """Add CLI template"""
        if not variables:
            variables = []
        if self._settings.adom == "global":
            url = "/pm/config/global/obj/cli/template"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template"
        request = {
            "data": {
                "description": description,
                "name": name,
                "provision": provision,
                "script": script,
                "type": type,
                "variables": [variable["name"] for variable in variables],
            },
            "url": url,
        }
        return self.add(request)

    def assign_cli_template(self, template: str, target: Union[Dict[str, str], List[Dict[str, str]]]):
        """Assign group or device to template

        Examples:
            target = {"name": "mygroup"}

            target = {"name": "myfw", "vdom": "root"}

            target = [ {"name": "group1"}, {"name": "group2"} ]

        Args:
            template: name of template
            target: a single object or a list of objects to assign to the template
        """
        if not isinstance(target, list):
            target = [target]

        if self._settings.adom == "global":
            url = f"/pm/config/global/obj/cli/template/{template}/scope member"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template/{template}/scope member"
        request = {"data": target, "url": url}
        return self.add(request)

    def assign_cli_template_group(self, template_group: str, target: Union[Dict[str, str], List[Dict[str, str]]]):
        """Assign group or device to template group

        Examples:
            target = {"name": "mygroup"}

            target = {"name": "myfw", "vdom": "root"}

            target = [ {"name": "group1"}, {"name": "group2"} ]

        Args:
            template_group: name of template
            target: a single object or a list of objects to assign to the template

        Raises:
            FMGInvalidDataException: if target is invalid or non-existent
        """
        if not isinstance(target, list):
            target = [target]

        if self._settings.adom == "global":
            url = f"/pm/config/global/obj/cli/template-group/{template_group}/scope member"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template-group/{template_group}/scope member"
        request = {"data": target, "url": url}
        return self.add(request)

    def update_cli_template(
        self,
        name: str,
        script: str,
        new_name: str = "",
        description: str = "",
        provision: Literal["disable", "enable"] = "disable",
        type: Literal["cli", "jinja"] = "jinja",
        variables: Optional[List[dict]] = None,
    ) -> FMGResponse:
        """Update a CLI template"""
        if not variables:
            variables = []
        if self._settings.adom == "global":
            url = f"/pm/config/global/obj/cli/template/{name}"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template/{name}"
        if new_name:
            name = new_name
        request = {
            "data": {
                "description": description,
                "name": name,
                "provision": provision,
                "script": script,
                "type": type,
                "variables": [variable["name"] for variable in variables],
            },
            "url": url,
        }
        return self.update(request)

    def set_cli_template(
        self,
        name: str,
        script: str,
        new_name: str = "",
        description: str = "",
        provision: Literal["disable", "enable"] = "disable",
        type: Literal["cli", "jinja"] = "jinja",
        variables: Optional[List[dict]] = None,
    ) -> FMGResponse:
        """Update a CLI template"""
        if not variables:
            variables = []
        if self._settings.adom == "global":
            url = f"/pm/config/global/obj/cli/template/{name}"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template/{name}"
        if new_name:
            name = new_name
        request = {
            "data": {
                "description": description,
                "name": name,
                "provision": provision,
                "script": script,
                "type": type,
                "variables": [variable["name"] for variable in variables],
            },
            "url": url,
        }
        return self.set(request)

    def get_cli_template(self, name: str) -> FMGResponse:
        """Get a specific CLI template"""
        if self._settings.adom == "global":
            url = f"/pm/config/global/obj/cli/template/{name}"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template/{name}"
        request = {
            "url": url,
            "option": "scope member",
        }
        return self.get(request)

    def get_cli_templates(self, filters: FILTER_TYPE = None) -> FMGResponse:
        """Get CLI templates"""
        if self._settings.adom == "global":
            url = "/pm/config/global/obj/cli/template"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template"

        request = {
            "url": url,
            "option": "scope member",
        }
        if filters:
            request["filter"] = self._get_filter_list(filters)
        return self.get(request)

    def delete_cli_template(self, name: str) -> FMGResponse:
        """Delete CLI template"""
        if self._settings.adom == "global":
            url = f"/pm/config/global/obj/cli/template/{name}"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template/{name}"
        request = {
            "url": url,
        }
        return self.delete(request)

    # Template group operations

    def add_cli_template_group(
        self,
        name: str,
        description: str = "",
        member: Optional[List[str]] = None,
        variables: Optional[List[dict]] = None,
    ) -> FMGResponse:
        """Add CLI template group"""
        if not variables:
            variables = []
        if not member:
            member = []
        if self._settings.adom == "global":
            url = "/pm/config/global/obj/cli/template-group"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template-group"
        request = {
            "data": {
                "description": description,
                "name": name,
                "member": member,
                "variables": [variable["name"] for variable in variables],
            },
            "url": url,
        }
        return self.add(request)

    def update_cli_template_group(
        self,
        name: str,
        description: str = "",
        member: Optional[List[str]] = None,
        variables: Optional[List[dict]] = None,
    ) -> FMGResponse:
        """Update CLI template group"""
        if not variables:
            variables = []
        if not member:
            member = []
        if self._settings.adom == "global":
            url = "/pm/config/global/obj/cli/template-group"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template-group"
        request = {
            "data": {
                "description": description,
                "name": name,
                "member": member,
                "variables": [variable["name"] for variable in variables],
            },
            "url": url,
        }
        return self.update(request)

    def set_cli_template_group(
        self,
        name: str,
        description: str = "",
        member: Optional[List[str]] = None,
        variables: Optional[List[dict]] = None,
    ) -> FMGResponse:
        """Set CLI template group"""
        if not variables:
            variables = []
        if not member:
            member = []
        if self._settings.adom == "global":
            url = "/pm/config/global/obj/cli/template-group"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template-group"
        request = {
            "data": {
                "description": description,
                "name": name,
                "member": member,
                "variables": [variable["name"] for variable in variables],
            },
            "url": url,
        }
        return self.set(request)

    def get_cli_template_group(self, name: str) -> FMGResponse:
        """Get a specific CLI template group"""
        if self._settings.adom == "global":
            url = f"/pm/config/global/obj/cli/template-group/{name}"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template-group/{name}"
        request = {
            "url": url,
            "option": "scope member",
        }
        return self.get(request)

    def get_cli_template_groups(self, filters: FILTER_TYPE = None) -> FMGResponse:
        """Get CLI template groups"""
        if self._settings.adom == "global":
            url = "/pm/config/global/obj/cli/template-group"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template-group"
        request = {
            "url": url,
            "option": "scope member",
        }
        if filters:
            request["filter"] = self._get_filter_list(filters)
        try:
            return self.get(request)
        except FMGEmptyResultException:
            return FMGResponse(data={"data": []})

    def delete_cli_template_group(self, name: str) -> FMGResponse:
        """Delete CLI template"""
        if self._settings.adom == "global":
            url = f"/pm/config/global/obj/cli/template-group/{name}"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template-group/{name}"
        request = {
            "url": url,
        }
        return self.delete(request)

    def add_fmg_variable(
        self, name: str, value: Optional[str] = None, description: Optional[str] = None
    ) -> FMGResponse:
        """Add metadata variable to use in CLI templates

        Args:
            name (str): variable name
            value (str): default value
            description (str): variable description
        """
        if self._settings.adom == "global":
            url = "/pm/config/global/obj/fmg/variable"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/fmg/variable"
        request = {
            "data": {
                "description": description,
                "name": name,
                "value": value,
            },
            "url": url,
        }
        return self.add(request)

    def get_fmg_variable(self, name: str) -> FMGResponse:
        """Get a specific variable"""
        if self._settings.adom == "global":
            url = f"/pm/config/global/obj/fmg/variable/{name}"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/fmg/variable/{name}"
        request = {
            "url": url,
        }
        return self.get(request)

    def get_fmg_variables(self, filters: FILTER_TYPE = None) -> FMGResponse:
        """Get metadata variables based on filter"""
        if self._settings.adom == "global":
            url = "/pm/config/global/obj/fmg/variable"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/fmg/variable"
        request = {
            "url": url,
        }
        if filters:
            request["filter"] = self._get_filter_list(filters)
        return self.get(request)

    def update_fmg_variable(
        self, name: str, value: Optional[str] = None, description: Optional[str] = None
    ) -> FMGResponse:
        """Update metadata variable to use in CLI templates

        Args:
            name (str): variable name
            value (str): default value
            description (str): variable description
        """
        if self._settings.adom == "global":
            url = "/pm/config/global/obj/fmg/variable"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/fmg/variable"
        request = {
            "data": {
                "description": description,
                "name": name,
                "value": value,
            },
            "url": url,
        }
        return self.update(request)

    def set_fmg_variable(
        self, name: str, value: Optional[str] = None, description: Optional[str] = None
    ) -> FMGResponse:
        """Update metadata variable to use in CLI templates

        Args:
            name (str): variable name
            value (str): default value
            description (str): variable description
        """
        if self._settings.adom == "global":
            url = "/pm/config/global/obj/fmg/variable"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/fmg/variable"
        request = {
            "data": {
                "description": description,
                "name": name,
                "value": value,
            },
            "url": url,
        }
        return self.set(request)

    def get_devices(self, filters: FILTER_TYPE = None):
        """Get devices"""
        if self._settings.adom == "global":
            url = "/dvmdb/device"
        else:
            url = f"/dvmdb/adom/{self._settings.adom}/device"

        request = {
            "url": url,
            "fields": ["name", "conf_status", "conn_status", "db_status", "dev_status"],
            "loadsub": 1,  # gather vdoms
            "option": [
                "extra info",
                "assignment info",
            ],
        }
        if filters:
            request["filter"] = self._get_filter_list(filters)
        return self.get(request)

    def get_group_members(self, group_name: str):
        """Get group members"""
        if self._settings.adom == "global":
            url = f"/dvmdb/group/{group_name}"
        else:
            url = f"/dvmdb/adom/{self._settings.adom}/group/{group_name}"

        request = {"option": "object member", "url": url}
        return self.get(request)
