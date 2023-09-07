"""Errors raised in the application"""


class FMGSyncException(Exception):
    """General FMG template sync error"""


class FMGSyncConfigurationException(FMGSyncException):
    """Error in configuration"""


class FMGSyncConnectionException(FMGSyncException):
    """Error while connecting to FMG"""
