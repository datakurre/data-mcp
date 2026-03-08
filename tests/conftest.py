"""Shared fixtures for data-mcp tests."""

import pytest

from data_mcp.store import TableStore, set_store


@pytest.fixture(autouse=True)
def fresh_store():
    """Reset the global table store singleton before every test."""
    set_store(TableStore())
