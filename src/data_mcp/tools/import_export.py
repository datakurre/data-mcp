"""Import and export tools for data-mcp."""

from __future__ import annotations

import os
from typing import Optional, Union

import pandas as pd
from fastmcp.utilities.types import ContentBlock

from data_mcp._helpers import table_response, text_response
from data_mcp.server import mcp
from data_mcp.store import get_store as _get_store


def _auto_name(file_path: str) -> str:
    """Derive a table name from a file path (stem without extension)."""
    return os.path.splitext(os.path.basename(file_path))[0]


def _is_xlsx(file_path: str) -> bool:
    return file_path.lower().endswith((".xlsx", ".xls", ".xlsm"))


@mcp.tool
def import_table(
    file_path: str,
    table_name: Optional[str] = None,
    sheet_name: Optional[Union[str, int]] = None,
    sep: str = ",",
    header: int = 0,
    encoding: str = "utf-8",
) -> list[ContentBlock]:
    """Import a CSV or XLSX file into the table store.

    Format is auto-detected from the file extension (.csv → CSV; .xlsx/.xls/.xlsm → Excel).

    Args:
        file_path: Path to the CSV or XLSX file.
        table_name: Name to register the table under (defaults to the filename stem).
        sheet_name: Sheet name or index to read from an XLSX file (default 0 = first sheet).
                    Ignored for CSV files.
        sep: Column separator for CSV files (default ',').
        header: Row number to use as column names for CSV files (default 0).
        encoding: File encoding for CSV files (default 'utf-8').
    """
    name = table_name or _auto_name(file_path)
    if _is_xlsx(file_path):
        sn = sheet_name if sheet_name is not None else 0
        df = pd.read_excel(file_path, sheet_name=sn, engine="openpyxl")
        msg = f"Imported '{name}' from {file_path} sheet '{sn}' ({df.shape[0]} rows × {df.shape[1]} cols)."
    else:
        df = pd.read_csv(file_path, sep=sep, header=header, encoding=encoding)
        msg = f"Imported '{name}' from {file_path} ({df.shape[0]} rows × {df.shape[1]} cols)."
    _get_store().add_table(name, df)
    return table_response(df, msg)


@mcp.tool
def export_table(
    table_names: Union[str, list[str]],
    file_path: str,
    sheet_name: str = "Sheet1",
    index: bool = False,
    sep: str = ",",
    encoding: str = "utf-8",
) -> list[ContentBlock]:
    """Export one or more tables to a CSV or XLSX file.

    Format is auto-detected from the file extension.
    - CSV: only a single table name is supported.
    - XLSX: a single name → one sheet; a list of names → one sheet per table.

    Args:
        table_names: Table name (str) or list of table names to export.
        file_path: Destination file path (.csv or .xlsx).
        sheet_name: Sheet name when exporting a single table to XLSX (default 'Sheet1').
        index: Whether to write the row index (default False).
        sep: Column separator for CSV export (default ',').
        encoding: File encoding for CSV export (default 'utf-8').
    """
    store = _get_store()
    names = [table_names] if isinstance(table_names, str) else list(table_names)

    if _is_xlsx(file_path):
        if len(names) == 1:
            df = store.get_table(names[0])
            df.to_excel(
                file_path, sheet_name=sheet_name, index=index, engine="openpyxl"
            )
            return text_response(
                f"Exported '{names[0]}' to {file_path} (sheet '{sheet_name}', {df.shape[0]} rows)."
            )
        else:
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                for name in names:
                    df = store.get_table(name)
                    df.to_excel(writer, sheet_name=name, index=index)
            return text_response(f"Exported sheets {names} to {file_path}.")
    else:
        if len(names) > 1:
            raise ValueError(
                "CSV format does not support multiple tables. Use an .xlsx path for multi-sheet export."
            )
        df = store.get_table(names[0])
        df.to_csv(file_path, index=index, sep=sep, encoding=encoding)
        return text_response(
            f"Exported '{names[0]}' to {file_path} ({df.shape[0]} rows)."
        )
