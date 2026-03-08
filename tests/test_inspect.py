"""Tests for inspection tools."""

import pandas as pd
import pytest

from data_mcp.store import get_store
from data_mcp.tools.inspect import info, list_tables, preview, value_counts


def _text(blocks) -> str:
    return blocks[0].text


@pytest.fixture(autouse=True)
def load_df():
    df = pd.DataFrame(
        {"name": ["Alice", "Bob", "Alice", "Charlie"], "score": [90, 80, 95, 70]}
    )
    get_store().add_table("scores", df)


def test_list_tables():
    result = list_tables()
    assert "scores" in _text(result)


def test_info_schema():
    result = info("scores", detail="schema")
    text = _text(result)
    assert "name" in text
    assert "score" in text


def test_info_shape():
    result = info("scores", detail="shape")
    text = _text(result)
    assert "4 rows" in text
    assert "2 columns" in text


def test_info_describe():
    result = info("scores", detail="describe")
    text = _text(result)
    assert "score" in text


def test_info_all():
    result = info("scores", detail="all")
    assert len(result) >= 2  # multiple content blocks


def test_info_invalid_raises():
    with pytest.raises(ValueError, match="Unknown detail"):
        info("scores", detail="bogus")


def test_preview_head():
    result = preview("scores", mode="head", n=2)
    text = _text(result)
    assert "Alice" in text


def test_preview_tail():
    result = preview("scores", mode="tail", n=1)
    text = _text(result)
    assert "Charlie" in text


def test_preview_sample():
    result = preview("scores", mode="sample", n=2)
    assert "score" in _text(result)


def test_preview_invalid_raises():
    with pytest.raises(ValueError, match="Unknown mode"):
        preview("scores", mode="bogus")


def test_value_counts():
    result = value_counts("scores", "name")
    text = _text(result)
    assert "Alice" in text
    assert "2" in text
