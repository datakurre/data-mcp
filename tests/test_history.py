"""Tests for the history (undo/redo) tool."""

import pandas as pd
import pytest

from data_mcp.store import get_store
from data_mcp.tools.history import history


def _text(blocks) -> str:
    return blocks[0].text


def test_undo_reverts_add_table():
    store = get_store()
    df1 = pd.DataFrame({"x": [1]})
    df2 = pd.DataFrame({"x": [99]})
    store.add_table("t", df1)
    store.add_table("t", df2)
    assert store.get_table("t")["x"].tolist() == [99]
    result = history(action="undo")
    assert store.get_table("t")["x"].tolist() == [1]


def test_redo_re_applies():
    store = get_store()
    df1 = pd.DataFrame({"x": [1]})
    df2 = pd.DataFrame({"x": [99]})
    store.add_table("t", df1)
    store.add_table("t", df2)
    history(action="undo")
    result = history(action="redo")
    assert store.get_table("t")["x"].tolist() == [99]


def test_undo_nothing():
    result = history(action="undo")
    assert "Nothing" in _text(result)


def test_redo_nothing():
    result = history(action="redo")
    assert "Nothing" in _text(result)


def test_invalid_action_raises():
    with pytest.raises(ValueError, match="action must be"):
        history(action="invalid")
