"""Errors raised in the application"""


class FMGSyncException(Exception):
    """General FMG template sync error"""


class FMGSyncConfigurationException(FMGSyncException):
    """Error in configuration"""


class FMGSyncConnectionException(FMGSyncException):
    """Error while connecting to FMG"""


class FMGSyncVariableException(FMGSyncException):
    """Error by variable definitions"""


class FMGSyncInvalidStatusException(FMGSyncException):
    """Unknown of invalid device status found"""


class FMGSyncDeleteError(FMGSyncException):
    """Error by deleting object"""
