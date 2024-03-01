"""Pytest setup"""

from pathlib import Path

import dotenv
import pytest
import requests

from fortimanager_template_sync.config import FMGSyncSettings


def pytest_addoption(parser):
    """Pytest options"""
    parser.addoption(
        "--lab_config", action="store", default="fmgsync.env", help="env file for lab setup (check online docs!)"
    )
    parser.addoption(
        "--keep-lab", action="store_true", help="keep created objects and do not discard workspace changes"
    )


def pytest_configure(config):
    """Pytest configuration"""
    pytest.lab_config_file = Path(config.getoption("--lab_config"))
    pytest.keep_lab = config.getoption("--keep-lab")
    pytest.lab_config = {}
    if pytest.lab_config_file.is_file():
        # yaml = YAML(typ="safe", pure=True)
        # lab_config = yaml.load(pytest.lab_config_file)
        dotenv.load_dotenv(pytest.lab_config_file)
        # settings will be taken from environment variables
        pytest.lab_config = FMGSyncSettings()


@pytest.fixture
def prepare_lab():
    """Prepare global lab settings"""
    # disable SSL warnings for testing
    # pylint: disable=no-member
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
