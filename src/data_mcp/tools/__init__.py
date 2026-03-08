"""Register all tool modules by importing them (side-effect: decorators run)."""

from data_mcp.tools import (
    batch,
    edit,
    history,
    import_export,
    inspect,
    transform,
    xlsx_edit,
)

__all__ = [
    "batch",
    "edit",
    "history",
    "import_export",
    "inspect",
    "transform",
    "xlsx_edit",
]
