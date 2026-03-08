"""Tests for data transformation tools."""

import pandas as pd
import pytest

from data_mcp.store import get_store
from data_mcp.tools.transform import (
    add_column,
    combine_tables,
    drop_duplicates,
    filter_rows,
    group_by,
    handle_na,
    rename_columns,
    reshape,
    select_columns,
    set_dtypes,
    sort_table,
)


def _text(blocks) -> str:
    return blocks[0].text


@pytest.fixture(autouse=True)
def load_df():
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "Alice"],
            "city": ["NY", "LA", "NY", "LA"],
            "score": [90, 80, 70, 85],
            "price": [10.0, 20.0, 30.0, None],
        }
    )
    get_store().add_table("t", df)


def test_filter_rows():
    filter_rows("t", "score > 80")
    df = get_store().get_table("t")
    assert all(df["score"] > 80)


def test_filter_rows_result_table():
    filter_rows("t", "score > 80", result_table="high")
    assert "high" in get_store().list_tables()
    assert "t" in get_store().list_tables()


def test_sort_table():
    sort_table("t", by="score", ascending=True)
    df = get_store().get_table("t")
    assert df["score"].tolist() == sorted(df["score"].tolist())


def test_select_columns_keep():
    select_columns("t", ["name", "score"])
    df = get_store().get_table("t")
    assert list(df.columns) == ["name", "score"]


def test_select_columns_exclude():
    select_columns("t", ["city"], exclude=True)
    df = get_store().get_table("t")
    assert "city" not in df.columns
    assert "name" in df.columns


def test_rename_columns():
    rename_columns("t", {"name": "person"})
    df = get_store().get_table("t")
    assert "person" in df.columns
    assert "name" not in df.columns


def test_add_column():
    add_column("t", "double_score", "score * 2")
    df = get_store().get_table("t")
    assert "double_score" in df.columns
    assert df["double_score"].tolist() == [180, 160, 140, 170]


def test_drop_duplicates():
    drop_duplicates("t", subset=["name"], keep="first")
    df = get_store().get_table("t")
    assert len(df) == 3


def test_handle_na_drop():
    handle_na("t", action="drop", subset=["price"])
    df = get_store().get_table("t")
    assert df["price"].isna().sum() == 0
    assert len(df) == 3


def test_handle_na_fill_value():
    handle_na("t", action="fill", value=0.0, column="price")
    df = get_store().get_table("t")
    assert df["price"].isna().sum() == 0


def test_handle_na_invalid_action():
    with pytest.raises(ValueError, match="Unknown action"):
        handle_na("t", action="bogus")


def test_set_dtypes():
    set_dtypes("t", {"score": "float64"})
    df = get_store().get_table("t")
    assert str(df["score"].dtype) == "float64"


def test_combine_tables_concat():
    df2 = pd.DataFrame(
        {"name": ["Dave"], "city": ["SF"], "score": [75], "price": [5.0]}
    )
    get_store().add_table("t2", df2)
    combine_tables(["t", "t2"], mode="concat", result_table="combined")
    df_c = get_store().get_table("combined")
    assert len(df_c) == 5


def test_combine_tables_merge():
    df2 = pd.DataFrame({"name": ["Alice", "Bob"], "country": ["US", "US"]})
    get_store().add_table("t2", df2)
    combine_tables(
        ["t", "t2"], mode="merge", on="name", how="inner", result_table="merged"
    )
    assert "merged" in get_store().list_tables()
    df_merged = get_store().get_table("merged")
    assert "country" in df_merged.columns


def test_combine_tables_merge_requires_two():
    get_store().add_table("t2", pd.DataFrame({"x": [1]}))
    get_store().add_table("t3", pd.DataFrame({"x": [2]}))
    with pytest.raises(ValueError, match="exactly 2"):
        combine_tables(["t", "t2", "t3"], mode="merge")


def test_combine_tables_invalid_mode():
    with pytest.raises(ValueError, match="Unknown mode"):
        combine_tables(["t"], mode="bogus")


def test_group_by():
    group_by("t", by="city", agg={"score": "mean"}, result_table="grouped")
    df = get_store().get_table("grouped")
    assert "score" in df.columns
    assert len(df) == 2


def test_reshape_pivot():
    reshape(
        "t",
        mode="pivot",
        index="city",
        columns="name",
        values="score",
        aggfunc="mean",
        result_table="piv",
    )
    assert "piv" in get_store().list_tables()


def test_reshape_melt():
    select_columns("t", ["name", "score"], result_table="narrow")
    reshape(
        "narrow",
        mode="melt",
        id_vars=["name"],
        value_vars=["score"],
        result_table="melted",
    )
    df = get_store().get_table("melted")
    assert "variable" in df.columns


def test_reshape_transpose():
    select_columns("t", ["score"], result_table="s")
    reshape("s", mode="transpose", result_table="transposed")
    df = get_store().get_table("transposed")
    assert df.shape[0] == 1


def test_reshape_pivot_missing_params():
    with pytest.raises(ValueError, match="requires"):
        reshape("t", mode="pivot")


def test_reshape_melt_missing_params():
    with pytest.raises(ValueError, match="requires"):
        reshape("t", mode="melt")


def test_reshape_invalid_mode():
    with pytest.raises(ValueError, match="Unknown mode"):
        reshape("t", mode="bogus")
