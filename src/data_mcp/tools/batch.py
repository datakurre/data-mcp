"""Batch tool — execute multiple data-mcp operations in a single round-trip."""

from __future__ import annotations

from typing import Any

from fastmcp.utilities.types import ContentBlock

from data_mcp._helpers import tables_list_response, text_response
from data_mcp.server import mcp


def _dispatch(tool_name: str, args: dict[str, Any]) -> list[ContentBlock]:
    """Look up the named tool's core function and call it."""
    # Lazy imports to avoid circular imports at module load time
    import data_mcp.tools.edit as _edit
    import data_mcp.tools.history as _history
    import data_mcp.tools.import_export as _ie
    import data_mcp.tools.inspect as _inspect
    import data_mcp.tools.transform as _transform
    import data_mcp.tools.xlsx_edit as _xlsx

    _tool_map: dict[str, Any] = {
        # import/export
        "import_table": _ie.import_table,
        "export_table": _ie.export_table,
        # inspect
        "list_tables": _inspect.list_tables,
        "info": _inspect.info,
        "preview": _inspect.preview,
        "value_counts": _inspect.value_counts,
        # transform
        "filter_rows": _transform.filter_rows,
        "sort_table": _transform.sort_table,
        "select_columns": _transform.select_columns,
        "rename_columns": _transform.rename_columns,
        "add_column": _transform.add_column,
        "drop_duplicates": _transform.drop_duplicates,
        "handle_na": _transform.handle_na,
        "set_dtypes": _transform.set_dtypes,
        "combine_tables": _transform.combine_tables,
        "group_by": _transform.group_by,
        "reshape": _transform.reshape,
        # edit
        "update_cells": _edit.update_cells,
        "edit_rows": _edit.edit_rows,
        "apply_formula": _edit.apply_formula,
        # xlsx
        "write_sheet": _xlsx.write_sheet,
        "manage_sheets": _xlsx.manage_sheets,
        # history
        "history": _history.history,
    }
    fn = _tool_map.get(tool_name)
    if fn is None:
        raise ValueError(
            f"Unknown tool '{tool_name}'. Available: {sorted(_tool_map.keys())}"
        )
    return fn(**args)


@mcp.tool
def batch(calls: list[dict]) -> list[ContentBlock]:
    """Execute multiple tool calls in a single round-trip.

    Each element of *calls* must be a dict with keys:
    - ``"tool"`` — the tool name (string)
    - ``"args"`` — dict of keyword arguments for that tool

    Returns the response from the last call, or a tables summary if the
    last call returned nothing useful.

    Example::

        batch(calls=[
            {"tool": "import_table", "args": {"file_path": "sales.csv", "table_name": "sales"}},
            {"tool": "filter_rows", "args": {"table_name": "sales", "query": "revenue > 1000"}},
            {"tool": "preview", "args": {"table_name": "sales", "n": 5}}
        ])
    """
    result: list[ContentBlock] = []
    for call in calls:
        tool_name = call.get("tool", "")
        args = call.get("args", {})
        result = _dispatch(tool_name, args)
    return result if result else tables_list_response()
