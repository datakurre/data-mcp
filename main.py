"""Entry point — delegates entirely to the data_mcp package."""

from data_mcp import mcp  # noqa: F401 — imports register all tools

if __name__ == "__main__":
    mcp.run(transport="stdio")
