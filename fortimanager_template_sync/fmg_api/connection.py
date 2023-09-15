"""FMG connection"""
import functools
import logging
from typing import Any, Optional

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
            try:  # try again after refreshing token
                self._token = self._get_token()  # pylint: disable=protected-access  # decorator of methods
                return func(self, *args, **kwargs)
            except FMGException as err2:
                raise err2 from err

    return decorated


class FMG:
    """Fortimanager connection class"""

    def __init__(self, settings: FMGSettings):
        logger.debug("Initializing connection to %s", settings.base_url)
        self._settings = settings
        self._token: Optional[SecretStr] = None
        self._session: Optional[requests.Session] = None

    def open(self):
        """open connection"""
        self._session = requests.Session()
        self._token = self._get_token()

    def close(self):
        """close connection"""
        # Logout and expire token
        request = {
            "id": 1,
            "method": "exec",
            "params": [{"url": "/sys/logout"}],
            "session": self._token.get_secret_value(),
        }
        try:
            req = self._session.post(self._settings.base_url, json=request, verify=self._settings.verify)
            status = req.json().get("result", [{}])[0].get("status", {})
            if status.get("code") != 0:
                logger.warning("Logout failed!")
        except requests.exceptions.ConnectionError:
            logger.warning("Logout failed!")

        self._session.close()
        logger.debug("Closed session")

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    def _post(self, request: dict) -> Any:
        req = self._session.post(self._settings.base_url, json=request, verify=self._settings.verify)
        results = req.json().get("result", [])
        if any(status := result["status"] for result in results if result["status"]["code"] != 0):
            raise FMGException(status)
        return results[0] if len(results) == 1 else results

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
        token = req.json().get("session", "")
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
        req = self._post(request)
        return req["data"]["Version"]
