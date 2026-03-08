"""Tests for import/export tools."""

import pandas as pd
import pytest

from data_mcp.store import get_store
from data_mcp.tools.import_export import export_table, import_table


def _text(blocks) -> str:
    return blocks[0].text


@pytest.fixture
def sample_csv(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("a,b\n1,x\n2,y\n")
    return str(p)


@pytest.fixture
def sample_xlsx(tmp_path):
    p = tmp_path / "data.xlsx"
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    df.to_excel(str(p), index=False, sheet_name="Sheet1")
    return str(p)


def test_import_csv_auto_name(sample_csv):
    result = import_table(sample_csv)
    store = get_store()
    assert "data" in store.list_tables()
    df = store.get_table("data")
    assert list(df.columns) == ["a", "b"]
    assert len(df) == 2
    assert "Imported" in _text(result)


def test_import_csv_custom_name(sample_csv):
    import_table(sample_csv, table_name="mytable")
    assert "mytable" in get_store().list_tables()


def test_import_xlsx(sample_xlsx):
    import_table(sample_xlsx, table_name="excel_tbl")
    df = get_store().get_table("excel_tbl")
    assert list(df.columns) == ["a", "b"]


def test_import_xlsx_sheet_by_name(sample_xlsx):
    import_table(sample_xlsx, table_name="s1", sheet_name="Sheet1")
    df = get_store().get_table("s1")
    assert len(df) == 2


def test_export_csv(tmp_path, sample_csv):
    import_table(sample_csv, table_name="t")
    out = str(tmp_path / "out.csv")
    result = export_table("t", out)
    assert "Exported" in _text(result)
    df2 = pd.read_csv(out)
    assert len(df2) == 2


def test_export_xlsx_single(tmp_path, sample_csv):
    import_table(sample_csv, table_name="t")
    out = str(tmp_path / "out.xlsx")
    result = export_table("t", out)
    assert "Exported" in _text(result)
    df2 = pd.read_excel(out)
    assert len(df2) == 2


def test_export_xlsx_multi(tmp_path, sample_csv):
    import_table(sample_csv, table_name="t1")
    import_table(sample_csv, table_name="t2")
    out = str(tmp_path / "multi.xlsx")
    result = export_table(["t1", "t2"], out)
    assert "Exported" in _text(result)
    import openpyxl

    wb = openpyxl.load_workbook(out)
    assert set(wb.sheetnames) == {"t1", "t2"}
    wb.close()


def test_export_csv_multi_raises(tmp_path, sample_csv):
    import_table(sample_csv, table_name="t1")
    import_table(sample_csv, table_name="t2")
    out = str(tmp_path / "out.csv")
    with pytest.raises(ValueError, match="CSV"):
        export_table(["t1", "t2"], out)
