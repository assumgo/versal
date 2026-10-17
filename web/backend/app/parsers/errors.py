"""Errors specific to the supported monthly statement scope."""


class UnsupportedLayoutError(ValueError):
    """A recognized report belongs to a family not supported by this reader."""
