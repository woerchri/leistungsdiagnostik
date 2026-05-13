from __future__ import annotations


class LDError(Exception):
    """Base class. Message must be a German, user-friendly sentence."""


class LDInputError(LDError):
    """User-facing: something is wrong with the input file."""


class LDProtocolError(LDError):
    """The Sportart in the input is not supported yet."""
