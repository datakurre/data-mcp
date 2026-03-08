"""Tests for data_mcp._helpers response builders."""

import pandas as pd
from mcp.types import TextContent

from data_mcp._helpers import table_response, tables_list_response, text_response
from data_mcp.store import get_store


def _text(blocks) -> str:
    return blocks[0].text


def test_text_response():
    blocks = text_response("hello")
    assert len(blocks) == 1
    assert isinstance(blocks[0], TextContent)
    assert "hello" in _text(blocks)


def test_table_response_contains_markdown():
    df = pd.DataFrame({"col": [1, 2, 3]})
    blocks = table_response(df, "My message")
    text = _text(blocks)
    assert "My message" in text
    assert "col" in text


def test_table_response_truncates():
    df = pd.DataFrame({"x": range(200)})
    blocks = table_response(df, max_rows=10)
    text = _text(blocks)
    assert "showing 10 of 200" in text


def test_tables_list_response_empty():
    blocks = tables_list_response()
    assert "No tables" in _text(blocks)


def test_tables_list_response_with_tables():
    store = get_store()
    store.add_table("sales", pd.DataFrame({"a": [1]}))
    blocks = tables_list_response()
    assert "sales" in _text(blocks)
