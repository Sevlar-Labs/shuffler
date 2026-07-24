"""Network poison: Connection drops and streaming termination."""

from __future__ import annotations


class ConnectionDroppedPoisonError(Exception):
    """Raised when connection drop poison is triggered."""

    pass
