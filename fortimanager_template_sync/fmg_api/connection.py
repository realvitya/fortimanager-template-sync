"""FMG connection"""
import logging
from typing import Optional, List, Literal, Union

from pyfortinet import FMG, FMGResponse
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
        variables: Optional[List[str]] = None,
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
                "variables": variables,
            },
            "url": url,
        }
        return self.add(request)

    def update_cli_template(
        self,
        name: str,
        script: str,
        new_name: str = "",
        description: str = "",
        provision: Literal["disable", "enable"] = "disable",
        type: Literal["cli", "jinja"] = "jinja",
        variables: Optional[List[str]] = None,
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
                "variables": variables,
            },
            "url": url,
        }
        return self.update(request)

    def get_cli_template(self, name: str) -> FMGResponse:
        """Get a specific CLI template"""
        if self._settings.adom == "global":
            url = f"/pm/config/global/obj/cli/template/{name}"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template/{name}"
        request = {
            "url": url,
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
        variables: Optional[List[str]] = None,
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
                "variables": variables,
            },
            "url": url,
        }
        return self.add(request)

    def update_cli_template_group(
        self,
        name: str,
        description: str = "",
        member: Optional[List[str]] = None,
        variables: Optional[List[str]] = None,
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
                "variables": variables,
            },
            "url": url,
        }
        return self.update(request)

    def get_cli_template_group(self, name: str) -> FMGResponse:
        """Get a specific CLI template group"""
        if self._settings.adom == "global":
            url = f"/pm/config/global/obj/cli/template-group/{name}"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template-group/{name}"
        request = {
            "url": url,
        }
        return self.get(request)

    def get_cli_template_groups(
        self,
        name_like: str = "",
    ) -> FMGResponse:
        """Get CLI template groups based on 'like' filter"""
        if self._settings.adom == "global":
            url = "/pm/config/global/obj/cli/template-group"
        else:
            url = f"/pm/config/adom/{self._settings.adom}/obj/cli/template-group"
        filter_list = []
        if name_like:
            filter_list.append(["name", "like", name_like])
        request = {
            "url": url,
            "filter": filter_list,
        }
        return self.get(request)

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
