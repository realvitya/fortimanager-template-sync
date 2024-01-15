"""Test FMG API features"""
import pytest

from fortimanager_template_sync.fmg_api.connection import FMGSync
from fortimanager_template_sync.fmg_api.data import CLITemplate, CLITemplateGroup

need_lab = pytest.mark.skipif(not pytest.lab_config, reason=f"Lab config {pytest.lab_config_file} does not exist!")


@need_lab
class TestFMGApi:
    """Lab tests"""

    fmg = FMGSync(**pytest.lab_config.get("fmg")).open()
    fmg_connected = pytest.mark.skipif(
        not fmg._token,
        reason=f"FMG {pytest.lab_config.get('fmg', {}).get('base_url')} is not connected!",
    )

    @fmg_connected
    def test_add_cli_template(self):
        response = self.fmg.add_cli_template(name="test_template", script="{# test #}")
        assert response.success

    @fmg_connected
    def test_get_cli_template(self):
        response = self.fmg.get_cli_template("test_template")
        assert response.success

    @fmg_connected
    def test_get_cli_templates(self):
        response = self.fmg.get_cli_templates(name_like="test_%")
        assert (
            "test_template" in (data["name"] for data in response.data.get("data")) and len(response.data["data"]) == 1
        )

    @fmg_connected
    def test_update_cli_template(self):
        response = self.fmg.update_cli_template(name="test_template", script="{# test2 #}")
        assert response.success

    @fmg_connected
    def test_get_updated_cli_template(self):
        response = self.fmg.get_cli_template("test_template")
        assert response.success
        cli_template = CLITemplate(**response.data.get("data"))
        assert cli_template.script == "{# test2 #}" and cli_template.type == "jinja"

    @fmg_connected
    def test_add_cli_template_group(self):
        response = self.fmg.add_cli_template_group(name="test_template_group", member=["test_template"])
        assert response.success

    @fmg_connected
    def test_get_cli_template_group(self):
        response = self.fmg.get_cli_template_group("test_template_group")
        assert response.success

    @fmg_connected
    def test_update_cli_template_group(self):
        response = self.fmg.update_cli_template_group(name="test_template_group", description="Updated")
        assert response.success

    @fmg_connected
    def test_get_updated_cli_template_group(self):
        response = self.fmg.get_cli_template_group("test_template_group")
        assert response.success
        cli_template_group = CLITemplateGroup(**response.data.get("data"))
        assert cli_template_group.description == "Updated"

    @fmg_connected
    def test_delete_cli_template_group(self):
        response = self.fmg.delete_cli_template_group("test_template_group")
        assert response.success

    @fmg_connected
    def test_delete_cli_template(self):
        response = self.fmg.delete_cli_template("test_template")
        assert response.success

    @fmg_connected
    def test_close_fmg(self):
        self.fmg.close(discard_changes=True)
