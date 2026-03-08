"""data_mcp — tabular data MCP server package."""

from data_mcp import tools as _tools  # noqa: F401 — registers all tools
from data_mcp.server import mcp
from data_mcp.store import get_store, set_store

__all__ = ["mcp", "get_store", "set_store"]
