"""Tests for the TableStore core class."""

import pandas as pd
import pytest

from data_mcp.store import TableStore, get_store, set_store


def make_df(**cols):
    return pd.DataFrame(cols)


def test_add_and_get_table():
    store = get_store()
    df = make_df(a=[1, 2, 3])
    store.add_table("t", df)
    assert "t" in store.list_tables()
    pd.testing.assert_frame_equal(store.get_table("t"), df)


def test_get_table_missing_raises():
    store = get_store()
    with pytest.raises(KeyError, match="not found"):
        store.get_table("missing")


def test_remove_table():
    store = get_store()
    store.add_table("t", make_df(x=[1]))
    assert store.remove_table("t")
    assert "t" not in store.list_tables()
    assert not store.remove_table("t")  # idempotent


def test_rename_table():
    store = get_store()
    df = make_df(x=[1])
    store.add_table("old", df)
    assert store.rename_table("old", "new")
    assert "new" in store.list_tables()
    assert "old" not in store.list_tables()


def test_undo_redo():
    store = get_store()
    df1 = make_df(a=[1])
    df2 = make_df(a=[2])
    store.add_table("t", df1)
    store.add_table("t", df2)
    assert store.get_table("t")["a"].tolist() == [2]
    store.undo()
    assert store.get_table("t")["a"].tolist() == [1]
    store.redo()
    assert store.get_table("t")["a"].tolist() == [2]


def test_undo_empty_returns_false():
    store = get_store()
    assert not store.undo()


def test_redo_empty_returns_false():
    store = get_store()
    assert not store.redo()


def test_has_table():
    store = get_store()
    store.add_table("t", make_df(x=[1]))
    assert store.has_table("t")
    assert not store.has_table("missing")
