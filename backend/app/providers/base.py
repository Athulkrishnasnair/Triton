"""Contracts for harbour data providers.

Provider implementations should return sourced records with recorded/updated
timestamps, freshness, confidence, and verification status. They must not
present demo data as live data.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class DataProvider(Protocol):
    """Common interface for operator, government, and prototype providers."""

    name: str

    def get_market_context(self, harbour_id: int) -> dict:
        """Return verified structured context for a harbour.

        TODO: settle the context schema alongside the Harbour OS domain models.
        """
        ...
