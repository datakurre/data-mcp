"""Tests for cell/row editing tools."""

import pandas as pd
import pytest

from data_mcp.store import get_store
from data_mcp.tools.edit import apply_formula, edit_rows, update_cells


def _text(blocks) -> str:
    return blocks[0].text


@pytest.fixture(autouse=True)
def load_df():
    df = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"], "score": [90, 80, 70]})
    get_store().add_table("t", df)


def test_update_cells_single():
    update_cells("t", [{"row": 0, "column": "score", "value": 100}])
    df = get_store().get_table("t")
    assert df.iloc[0]["score"] == 100


def test_update_cells_multi():
    update_cells(
        "t",
        [
            {"row": 0, "column": "name", "value": "Alicia"},
            {"row": 1, "column": "score", "value": 99},
        ],
    )
    df = get_store().get_table("t")
    assert df.iloc[0]["name"] == "Alicia"
    assert df.iloc[1]["score"] == 99


def test_edit_rows_insert_end():
    edit_rows("t", action="insert", row_data={"name": "Dave", "score": 60})
    df = get_store().get_table("t")
    assert len(df) == 4
    assert df.iloc[-1]["name"] == "Dave"


def test_edit_rows_insert_at_index():
    edit_rows("t", action="insert", row_data={"name": "Dave", "score": 60}, index=1)
    df = get_store().get_table("t")
    assert df.iloc[1]["name"] == "Dave"


def test_edit_rows_delete():
    edit_rows("t", action="delete", indices=[0, 2])
    df = get_store().get_table("t")
    assert len(df) == 1
    assert df.iloc[0]["name"] == "Bob"


def test_edit_rows_replace():
    edit_rows("t", action="replace", column="name", to_replace="Alice", value="Alicia")
    df = get_store().get_table("t")
    assert "Alicia" in df["name"].values
    assert "Alice" not in df["name"].values


def test_edit_rows_insert_missing_row_data():
    with pytest.raises(ValueError, match="row_data"):
        edit_rows("t", action="insert")


def test_edit_rows_delete_missing_indices():
    with pytest.raises(ValueError, match="indices"):
        edit_rows("t", action="delete")


def test_edit_rows_replace_missing_column():
    with pytest.raises(ValueError, match="column"):
        edit_rows("t", action="replace", to_replace="Alice")


def test_edit_rows_invalid_action():
    with pytest.raises(ValueError, match="Unknown action"):
        edit_rows("t", action="bogus")


def test_apply_formula():
    apply_formula("t", "score", "col * 2")
    df = get_store().get_table("t")
    assert df.iloc[0]["score"] == 180
