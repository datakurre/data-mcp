"""Table inspection tools for data-mcp."""

from __future__ import annotations

import pandas as pd
from fastmcp.utilities.types import ContentBlock

from data_mcp._helpers import table_response, tables_list_response, text_response
from data_mcp.server import mcp
from data_mcp.store import get_store as _get_store


@mcp.tool
def list_tables() -> list[ContentBlock]:
    """List all loaded tables with their shape and column types."""
    return tables_list_response()


@mcp.tool
def info(table_name: str, detail: str = "schema") -> list[ContentBlock]:
    """Return metadata about a table.

    Args:
        table_name: Name of the table to inspect.
        detail: Level of detail — 'schema' (column names, dtypes, null counts; default),
                'shape' (row and column counts only),
                'describe' (df.describe() statistics),
                'all' (schema + shape + describe combined).
    """
    df = _get_store().get_table(table_name)

    if detail == "shape":
        r, c = df.shape
        return text_response(f"'{table_name}': {r} rows × {c} columns")

    if detail == "describe":
        desc = df.describe(include="all")
        return table_response(desc, f"Description of '{table_name}':")

    if detail in ("schema", "all"):
        schema_df = pd.DataFrame(
            {
                "dtype": df.dtypes.astype(str),
                "non_null": df.count(),
                "null": df.isna().sum(),
            }
        )
        msg = f"Schema of '{table_name}' ({df.shape[0]} rows × {df.shape[1]} cols):"
        if detail == "schema":
            return table_response(schema_df, msg)
        # "all" — combine schema + describe
        r, c = df.shape
        desc = df.describe(include="all")
        from mcp.types import TextContent

        blocks = [TextContent(type="text", text=f"{msg}\n\n{schema_df.to_markdown()}")]
        blocks += table_response(desc, f"\nDescribe statistics ({r} rows × {c} cols):")
        return blocks

    raise ValueError(
        f"Unknown detail '{detail}'. Must be one of: 'schema', 'shape', 'describe', 'all'."
    )


@mcp.tool
def preview(table_name: str, mode: str = "head", n: int = 10) -> list[ContentBlock]:
    """Return a preview of rows from a table.

    Args:
        table_name: Name of the table.
        mode: Which rows to return — 'head' (first N; default), 'tail' (last N), 'sample' (random N).
        n: Number of rows (default 10).
    """
    df = _get_store().get_table(table_name)
    if mode == "head":
        result = df.head(n)
        label = f"First {n} rows"
    elif mode == "tail":
        result = df.tail(n)
        label = f"Last {n} rows"
    elif mode == "sample":
        result = df.sample(min(n, len(df)))
        label = f"Random sample ({n} rows)"
    else:
        raise ValueError(f"Unknown mode '{mode}'. Must be 'head', 'tail', or 'sample'.")
    return table_response(result, f"{label} of '{table_name}':")


@mcp.tool
def value_counts(table_name: str, column: str) -> list[ContentBlock]:
    """Return a frequency table for a column.

    Args:
        table_name: Name of the table.
        column: Column name to count values for.
    """
    df = _get_store().get_table(table_name)
    vc = df[column].value_counts().reset_index()
    vc.columns = [column, "count"]
    return table_response(vc, f"Value counts for '{column}' in '{table_name}':")
