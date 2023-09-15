"""Pytest setup"""
from pathlib import Path

import pytest
import requests
from ruamel.yaml import YAML


def pytest_addoption(parser):
    """Pytest options"""
    parser.addoption("--lab_config", action="store", default="lab-config.yml")


def pytest_configure(config):
    """Pytest configuration"""
    pytest.lab_config_file = Path(config.getoption("--lab_config"))
    pytest.lab_config = {}
    if pytest.lab_config_file.is_file():
        yaml = YAML(typ="safe", pure=True)
        lab_config = yaml.load(pytest.lab_config_file)
        pytest.lab_config = lab_config


@pytest.fixture
def prepare_lab():
    """Prepare global lab settings"""
    # disable SSL warnings for testing
    # pylint: disable=no-member
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
