"""FMG connection"""
import functools
import logging
from typing import Optional

import requests
from pydantic import SecretStr

from fortimanager_template_sync.fmg_api.exceptions import FMGException, FMGTokenException
from fortimanager_template_sync.fmg_api.settings import FMGSettings

logger = logging.getLogger(__name__)


def auth_required(func):
    """decorator to provide authentication for the method"""
    @functools.wraps(func)
    def decorated(self, *args, **kwargs):
        """method which needs authentication"""
        if not self._token:  # pylint: disable=protected-access
            raise FMGTokenException("No token was obtained. Open connection first!")
        try:
            return func(self, *args, **kwargs)
        except FMGException as err:
            raise err

    return decorated


class FMG:
    """Fortimanager connection class"""

    def __init__(self, settings: FMGSettings):
        logger.debug("Initializing connection to %s", settings.base_url)
        self._settings = settings
        self._token: Optional[SecretStr] = None
        self._session = requests.Session()

    def open(self):
        """open connection"""
        self._token = self._get_token()

    def close(self):
        """close connection"""
        self._session.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    def _get_token(self) -> SecretStr:
        """Get authentication token

        Raises:

        """
        logger.debug("Getting token..")
        request = {
            "id": 1,
            "method": "exec",
            "params": [
                {
                    "data": {"passwd": self._settings.password.get_secret_value(), "user": self._settings.username},
                    "url": "/sys/login/user",
                }
            ],
        }
        try:
            req = self._session.post(self._settings.base_url, json=request, verify=self._settings.verify)
            status = req.json().get("result", [{}])[0].get("status", {})
            if status.get("code") != 0:
                raise FMGTokenException("Login failed, wrong credentials!")
            logger.debug("Token obtained")
        except FMGTokenException as err:
            logger.error("Can't gather token: %s", err)
            raise err
        except requests.exceptions.ConnectionError as err:
            logger.error("Can't gather token: %s", err)
            raise err
        token = req.json().get("session")
        return SecretStr(token)

    @auth_required
    def get_version(self) -> str:
        """Gather FMG version"""
        request = {
            "method": "get",
            "params": [{"url": "/sys/status"}],
            "id": 1,
            "session": self._token.get_secret_value(),
        }
        req = self._session.post(self._settings.base_url, json=request, verify=self._settings.verify)
        return req.json().get("result")[0].get("data").get("Version")
