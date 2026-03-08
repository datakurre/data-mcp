"""Shared response builders for data-mcp tools."""

from __future__ import annotations

from typing import Optional

import pandas as pd
from fastmcp.utilities.types import ContentBlock
from mcp.types import TextContent

from data_mcp.store import get_store as _get_store

_MAX_ROWS = 100  # max rows shown in a table preview


def table_response(
    df: pd.DataFrame,
    message: str = "",
    max_rows: int = _MAX_ROWS,
) -> list[ContentBlock]:
    """Return a text ContentBlock with *df* rendered as Markdown."""
    parts: list[str] = []
    if message:
        parts.append(message)
    truncated = df.head(max_rows)
    parts.append(truncated.to_markdown(index=True))
    if len(df) > max_rows:
        parts.append(f"_(showing {max_rows} of {len(df)} rows)_")
    return [TextContent(type="text", text="\n\n".join(parts))]


def text_response(message: str) -> list[ContentBlock]:
    """Return a plain text ContentBlock."""
    return [TextContent(type="text", text=message)]


def tables_list_response() -> list[ContentBlock]:
    """Return a summary of all tables in the store."""
    store = _get_store()
    names = store.list_tables()
    if not names:
        return text_response("No tables loaded.")
    lines = ["**Loaded tables:**\n"]
    for name in names:
        df = store.get_table(name)
        dtypes_str = ", ".join(f"{col}: {dt}" for col, dt in df.dtypes.items())
        lines.append(
            f"- **{name}** — {df.shape[0]} rows × {df.shape[1]} cols | {dtypes_str}"
        )
    return text_response("\n".join(lines))
