"""Data transformation tools for data-mcp."""

from __future__ import annotations

from typing import Optional, Union

import pandas as pd
from fastmcp.utilities.types import ContentBlock

from data_mcp._helpers import table_response, text_response
from data_mcp.server import mcp
from data_mcp.store import get_store as _get_store


def _save(name: str, result_table: Optional[str], df: pd.DataFrame) -> str:
    """Save df to result_table if given, otherwise overwrite name. Returns saved name."""
    target = result_table or name
    _get_store().add_table(target, df)
    return target


@mcp.tool
def filter_rows(
    table_name: str,
    query: str,
    result_table: Optional[str] = None,
) -> list[ContentBlock]:
    """Filter rows using a pandas query string.

    Args:
        table_name: Source table name.
        query: Pandas query expression (e.g. "age > 30 and city == 'London'").
        result_table: Name to store the result (overwrites source if omitted).
    """
    df = _get_store().get_table(table_name)
    result = df.query(query)
    target = _save(table_name, result_table, result)
    return table_response(
        result, f"Filtered '{table_name}' → '{target}' ({len(result)} rows)."
    )


@mcp.tool
def sort_table(
    table_name: str,
    by: Union[str, list[str]],
    ascending: Union[bool, list[bool]] = True,
    result_table: Optional[str] = None,
) -> list[ContentBlock]:
    """Sort a table by one or more columns.

    Args:
        table_name: Source table name.
        by: Column name or list of column names to sort by.
        ascending: Sort direction; True = ascending (default).
        result_table: Name to store the result (overwrites source if omitted).
    """
    df = _get_store().get_table(table_name)
    result = df.sort_values(by=by, ascending=ascending)
    target = _save(table_name, result_table, result)
    return table_response(result, f"Sorted '{table_name}' by {by} → '{target}'.")


@mcp.tool
def select_columns(
    table_name: str,
    columns: list[str],
    exclude: bool = False,
    result_table: Optional[str] = None,
) -> list[ContentBlock]:
    """Keep or drop specified columns.

    Args:
        table_name: Source table name.
        columns: List of column names to keep (or drop when exclude=True).
        exclude: If False (default), keep only the listed columns.
                 If True, drop the listed columns instead.
        result_table: Name to store the result (overwrites source if omitted).
    """
    df = _get_store().get_table(table_name)
    result = df.drop(columns=columns) if exclude else df[columns]
    target = _save(table_name, result_table, result)
    action = "Dropped columns" if exclude else "Selected columns"
    return table_response(
        result, f"{action} {columns} from '{table_name}' → '{target}'."
    )


@mcp.tool
def rename_columns(
    table_name: str,
    mapping: dict[str, str],
) -> list[ContentBlock]:
    """Rename columns using a mapping dict (in-place).

    Args:
        table_name: Table name to modify.
        mapping: Dict of {old_name: new_name}.
    """
    df = _get_store().get_table(table_name)
    result = df.rename(columns=mapping)
    _get_store().add_table(table_name, result)
    return table_response(result, f"Renamed columns in '{table_name}': {mapping}.")


@mcp.tool
def add_column(
    table_name: str,
    column_name: str,
    expression: str,
) -> list[ContentBlock]:
    """Add a new column using a pandas eval expression.

    Args:
        table_name: Table name to modify.
        column_name: Name for the new column.
        expression: Pandas eval expression referencing existing columns (e.g. "price * quantity").
    """
    df = _get_store().get_table(table_name)
    df = df.copy()
    df[column_name] = df.eval(expression)
    _get_store().add_table(table_name, df)
    return table_response(df, f"Added column '{column_name}' to '{table_name}'.")


@mcp.tool
def drop_duplicates(
    table_name: str,
    subset: Optional[list[str]] = None,
    keep: str = "first",
) -> list[ContentBlock]:
    """Drop duplicate rows.

    Args:
        table_name: Table name to modify.
        subset: Columns to consider for duplicates (all columns if omitted).
        keep: Which duplicate to keep: 'first', 'last', or False to drop all.
    """
    df = _get_store().get_table(table_name)
    before = len(df)
    result = df.drop_duplicates(subset=subset, keep=keep)
    _get_store().add_table(table_name, result)
    return table_response(
        result, f"Dropped {before - len(result)} duplicate rows from '{table_name}'."
    )


@mcp.tool
def handle_na(
    table_name: str,
    action: str = "drop",
    subset: Optional[list[str]] = None,
    value: Optional[Union[str, int, float]] = None,
    method: Optional[str] = None,
    column: Optional[str] = None,
) -> list[ContentBlock]:
    """Drop or fill NA/NaN values.

    Args:
        table_name: Table name to modify.
        action: 'drop' to remove rows with NAs (default); 'fill' to replace NAs with a value or method.
        subset: For action='drop': columns to check for NAs (all columns if omitted).
                For action='fill': ignored (use column param instead to restrict filling).
        value: Scalar fill value (used when action='fill').
        method: Pandas fill method: 'ffill' or 'bfill' (used when action='fill').
        column: Restrict fill action to this column; fills all columns if omitted.
    """
    df = _get_store().get_table(table_name).copy()

    if action == "drop":
        before = len(df)
        df = df.dropna(subset=subset)
        _get_store().add_table(table_name, df)
        return table_response(
            df, f"Dropped {before - len(df)} rows with NAs from '{table_name}'."
        )

    if action == "fill":
        if column:
            if method:
                df[column] = (
                    df[column].ffill() if method == "ffill" else df[column].bfill()
                )
            elif value is not None:
                df[column] = df[column].fillna(value)
        else:
            if method:
                df = df.ffill() if method == "ffill" else df.bfill()
            elif value is not None:
                df = df.fillna(value)
        _get_store().add_table(table_name, df)
        return table_response(df, f"Filled NAs in '{table_name}'.")

    raise ValueError(f"Unknown action '{action}'. Must be 'drop' or 'fill'.")


@mcp.tool
def set_dtypes(
    table_name: str,
    dtypes: dict[str, str],
) -> list[ContentBlock]:
    """Cast column types.

    Args:
        table_name: Table name to modify.
        dtypes: Dict of {column: dtype_string} (e.g. {"age": "int64", "price": "float64"}).
    """
    df = _get_store().get_table(table_name).copy()
    df = df.astype(dtypes)
    _get_store().add_table(table_name, df)
    return table_response(df, f"Cast column types in '{table_name}': {dtypes}.")


@mcp.tool
def combine_tables(
    table_names: list[str],
    mode: str = "concat",
    result_table: Optional[str] = None,
    on: Optional[Union[str, list[str]]] = None,
    how: str = "inner",
    axis: int = 0,
) -> list[ContentBlock]:
    """Concatenate or merge tables.

    Args:
        table_names: List of table names to combine.
                     For mode='merge', exactly two names are required.
        mode: 'concat' (default) — stack tables with pd.concat();
              'merge' — join two tables with pd.merge().
        result_table: Name for the result (auto-generated if omitted).
        on: Column(s) to join on (required for mode='merge').
        how: Join type for merge: 'inner', 'left', 'right', 'outer' (default 'inner').
        axis: Concatenation axis for concat: 0 = rows (default), 1 = columns.
    """
    store = _get_store()

    if mode == "concat":
        dfs = [store.get_table(n) for n in table_names]
        result = pd.concat(dfs, axis=axis, ignore_index=(axis == 0))
        target = result_table or f"{table_names[0]}_concat"
        store.add_table(target, result)
        return table_response(
            result,
            f"Concatenated {table_names} → '{target}' ({result.shape[0]} rows × {result.shape[1]} cols).",
        )

    if mode == "merge":
        if len(table_names) != 2:
            raise ValueError("mode='merge' requires exactly 2 table names.")
        left, right = table_names
        df_left = store.get_table(left)
        df_right = store.get_table(right)
        result = pd.merge(df_left, df_right, on=on, how=how)
        target = result_table or f"{left}_merged"
        store.add_table(target, result)
        return table_response(
            result,
            f"Merged '{left}' + '{right}' ({how}) on {on} → '{target}' ({len(result)} rows).",
        )

    raise ValueError(f"Unknown mode '{mode}'. Must be 'concat' or 'merge'.")


@mcp.tool
def group_by(
    table_name: str,
    by: Union[str, list[str]],
    agg: dict[str, str],
    result_table: Optional[str] = None,
) -> list[ContentBlock]:
    """Group by columns and aggregate.

    Args:
        table_name: Source table name.
        by: Column(s) to group by.
        agg: Dict of {column: aggregation_func} (e.g. {"revenue": "sum", "count": "size"}).
        result_table: Name for the result (overwrites source if omitted).
    """
    df = _get_store().get_table(table_name)
    result = df.groupby(by).agg(agg).reset_index()
    target = _save(table_name, result_table, result)
    return table_response(
        result, f"Grouped '{table_name}' by {by} with {agg} → '{target}'."
    )


@mcp.tool
def reshape(
    table_name: str,
    mode: str,
    result_table: Optional[str] = None,
    index: Optional[Union[str, list[str]]] = None,
    columns: Optional[str] = None,
    values: Optional[str] = None,
    aggfunc: str = "mean",
    id_vars: Optional[list[str]] = None,
    value_vars: Optional[list[str]] = None,
) -> list[ContentBlock]:
    """Reshape a table by pivoting, melting, or transposing.

    Args:
        table_name: Source table name.
        mode: Reshape operation — 'pivot', 'melt', or 'transpose'.
        result_table: Name for the result (overwrites source if omitted).
        index: For mode='pivot': column(s) to use as row index.
        columns: For mode='pivot': column to pivot into columns.
        values: For mode='pivot': column to aggregate.
        aggfunc: For mode='pivot': aggregation function (default 'mean').
        id_vars: For mode='melt': columns to keep as identifier variables.
        value_vars: For mode='melt': columns to unpivot (all non-id_vars if omitted).
    """
    df = _get_store().get_table(table_name)

    if mode == "pivot":
        if index is None or columns is None or values is None:
            raise ValueError("mode='pivot' requires 'index', 'columns', and 'values'.")
        result = df.pivot_table(
            index=index, columns=columns, values=values, aggfunc=aggfunc
        ).reset_index()
        target = _save(table_name, result_table, result)
        return table_response(result, f"Pivot table of '{table_name}' → '{target}'.")

    if mode == "melt":
        if id_vars is None:
            raise ValueError("mode='melt' requires 'id_vars'.")
        result = df.melt(id_vars=id_vars, value_vars=value_vars)
        target = _save(table_name, result_table, result)
        return table_response(result, f"Melted '{table_name}' → '{target}'.")

    if mode == "transpose":
        result = df.transpose()
        target = _save(table_name, result_table, result)
        return table_response(result, f"Transposed '{table_name}' → '{target}'.")

    raise ValueError(f"Unknown mode '{mode}'. Must be 'pivot', 'melt', or 'transpose'.")
