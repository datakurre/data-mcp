"""Tests for the batch tool."""

import pandas as pd
import pytest

from data_mcp.store import get_store
from data_mcp.tools.batch import batch


def _text(blocks) -> str:
    return blocks[0].text


@pytest.fixture
def sample_csv(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("a,b\n1,x\n2,y\n3,z\n")
    return str(p)


def test_batch_import_and_preview(sample_csv):
    result = batch(
        [
            {
                "tool": "import_table",
                "args": {"file_path": sample_csv, "table_name": "data"},
            },
            {"tool": "preview", "args": {"table_name": "data", "n": 2}},
        ]
    )
    assert "data" in get_store().list_tables()
    assert "a" in _text(result)


def test_batch_empty_returns_tables_list():
    result = batch([])
    assert isinstance(result, list)


def test_batch_unknown_tool_raises():
    with pytest.raises(ValueError, match="Unknown tool"):
        batch([{"tool": "does_not_exist", "args": {}}])


def test_batch_filter_and_sort():
    df = pd.DataFrame({"score": [90, 70, 80]})
    get_store().add_table("scores", df)
    result = batch(
        [
            {
                "tool": "filter_rows",
                "args": {"table_name": "scores", "query": "score >= 80"},
            },
            {
                "tool": "sort_table",
                "args": {"table_name": "scores", "by": "score", "ascending": False},
            },
            {"tool": "preview", "args": {"table_name": "scores", "n": 5}},
        ]
    )
    df_out = get_store().get_table("scores")
    assert all(df_out["score"] >= 80)
