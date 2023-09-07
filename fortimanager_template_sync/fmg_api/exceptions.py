"""FMG API exceptions"""


class FMGException(Exception):
    """General FMG error"""


class FMGTokenException(FMGException):
    """No Token error"""


class FMGAuthenticationException(FMGException):
    """Authentication error"""
