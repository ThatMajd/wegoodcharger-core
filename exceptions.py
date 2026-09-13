"""Exceptions raised by the cloud client."""


class FeatureNotImplementedError(NotImplementedError):
    """A requested feature or scenario has not been implemented yet."""


class APIError(Exception):
    """The API returned missing, invalid, or unexpected data."""
