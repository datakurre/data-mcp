"""Cell and row editing tools for data-mcp."""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd
from fastmcp.utilities.types import ContentBlock

from data_mcp._helpers import table_response, text_response
from data_mcp.server import mcp
from data_mcp.store import get_store as _get_store


@mcp.tool
def update_cells(
    table_name: str,
    updates: list[dict],
) -> list[ContentBlock]:
    """Set one or more cell values by integer row index and column name.

    Each entry in updates must have keys: 'row' (int, 0-based), 'column' (str), 'value'.
    To update a single cell, pass a list with one entry.

    Args:
        table_name: Name of the table to edit.
        updates: List of dicts with keys 'row' (int), 'column' (str), 'value'.
    """
    store = _get_store()
    df = store.get_table(table_name).copy()
    for upd in updates:
        r, col, val = upd["row"], upd["column"], upd["value"]
        df.iloc[r, df.columns.get_loc(col)] = val
    store.add_table(table_name, df)
    return table_response(
        df, f"Applied {len(updates)} cell update(s) to '{table_name}'."
    )


@mcp.tool
def edit_rows(
    table_name: str,
    action: str,
    row_data: Optional[dict] = None,
    index: Optional[int] = None,
    indices: Optional[list[int]] = None,
    column: Optional[str] = None,
    to_replace: Optional[Any] = None,
    value: Optional[Any] = None,
) -> list[ContentBlock]:
    """Insert rows, delete rows, or replace values in a column.

    Args:
        table_name: Name of the table to edit.
        action: Operation — 'insert', 'delete', or 'replace'.
        row_data: For action='insert': dict of {column: value} for the new row.
        index: For action='insert': row position to insert at (appends to end if omitted).
        indices: For action='delete': list of integer row index positions (0-based) to remove.
        column: For action='replace': column to apply replacement in.
        to_replace: For action='replace': value (or list/dict) to replace.
        value: For action='replace': replacement value.
    """
    store = _get_store()
    df = store.get_table(table_name).copy()

    if action == "insert":
        if row_data is None:
            raise ValueError("action='insert' requires 'row_data'.")
        new_row = pd.DataFrame([row_data])
        if index is None or index >= len(df):
            result = pd.concat([df, new_row], ignore_index=True)
        else:
            result = pd.concat(
                [df.iloc[:index], new_row, df.iloc[index:]], ignore_index=True
            )
        store.add_table(table_name, result)
        return table_response(
            result, f"Inserted row at index {index} into '{table_name}'."
        )

    if action == "delete":
        if not indices:
            raise ValueError(
                "action='delete' requires 'indices' (list of row positions)."
            )
        result = df.drop(index=df.index[indices]).reset_index(drop=True)
        store.add_table(table_name, result)
        return table_response(
            result, f"Deleted {len(indices)} row(s) from '{table_name}'."
        )

    if action == "replace":
        if column is None or to_replace is None:
            raise ValueError("action='replace' requires 'column' and 'to_replace'.")
        df[column] = df[column].replace(to_replace, value)
        store.add_table(table_name, df)
        return table_response(
            df, f"Replaced values in column '{column}' of '{table_name}'."
        )

    raise ValueError(
        f"Unknown action '{action}'. Must be 'insert', 'delete', or 'replace'."
    )


@mcp.tool
def apply_formula(
    table_name: str,
    column: str,
    expression: str,
) -> list[ContentBlock]:
    """Apply a pandas expression to a column, replacing its values.

    The expression is evaluated with `col` bound to the column Series.
    Example expressions: `col.str.upper()`, `col * 2`, `col.fillna(0)`.

    Args:
        table_name: Name of the table to edit.
        column: Column to transform.
        expression: Python expression referencing `col` (the column Series).
    """
    store = _get_store()
    df = store.get_table(table_name).copy()
    col = df[column]  # noqa: F841 — available inside eval
    df[column] = eval(expression)  # noqa: S307
    store.add_table(table_name, df)
    return table_response(
        df, f"Applied formula to column '{column}' in '{table_name}'."
    )
