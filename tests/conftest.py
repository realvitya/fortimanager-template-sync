"""Pytest setup"""
from pathlib import Path

import pytest
import requests
from ruamel.yaml import YAML


def pytest_addoption(parser):
    parser.addoption("--lab_config", action="store", default="lab-config.yml")


def pytest_configure(config):
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    pytest.lab_config_file = Path(config.getoption("--lab_config"))
    pytest.lab_config = None
    if pytest.lab_config_file.is_file():
        yaml = YAML(typ="safe", pure=True)
        lab_config = yaml.load(pytest.lab_config_file)
        pytest.lab_config = lab_config
