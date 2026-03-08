"""Undo/redo history tools for data-mcp."""

from __future__ import annotations

from fastmcp.utilities.types import ContentBlock

from data_mcp._helpers import tables_list_response, text_response
from data_mcp.server import mcp
from data_mcp.store import get_store as _get_store


@mcp.tool
def history(action: str = "undo") -> list[ContentBlock]:
    """Undo or redo the last table store change.

    Args:
        action: 'undo' to revert the last change, 'redo' to re-apply it.
    """
    store = _get_store()
    if action == "undo":
        ok = store.undo()
        verb = "Undone"
    elif action == "redo":
        ok = store.redo()
        verb = "Redone"
    else:
        raise ValueError(f"action must be 'undo' or 'redo', got '{action}'")
    if not ok:
        return text_response(f"Nothing to {action}.")
    return tables_list_response()
