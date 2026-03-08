# AGENTS.md — data-mcp developer guide for AI agents

This file is the primary reference for AI coding agents (Copilot, Claude, etc.) working inside this repository. Read it before making any changes.

---

## What this project is

`data-mcp` is a [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that exposes a **persistent in-memory table store** as a set of tool calls. Every tool returns a Markdown-formatted text response so the calling agent can inspect data after each step. The server is built with [FastMCP](https://github.com/jlowin/fastmcp) and uses pandas + openpyxl for all data work.

---

## Repository layout

```
main.py                          Entry point — runs the MCP server over stdio
pyproject.toml                   Package metadata and dependencies
src/
  data_mcp/
    __init__.py                  Imports tools (side-effect: registers them) + re-exports mcp
    server.py                    FastMCP instance + system-prompt INSTRUCTIONS string
    store.py                     TableStore class, global singleton, get_store()/set_store()
    _helpers.py                  table_response(), text_response(), tables_list_response()
    tools/
      __init__.py                Imports all tool sub-modules to trigger @mcp.tool() registration
      import_export.py           import_table, export_table
      inspect.py                 list_tables, info, preview, value_counts
      transform.py               filter_rows, sort_table, select_columns,
                                 rename_columns, add_column, drop_duplicates, handle_na,
                                 set_dtypes, combine_tables, group_by, reshape
      edit.py                    update_cells, edit_rows, apply_formula
      xlsx_edit.py               write_sheet, manage_sheets
      batch.py                   batch(calls) — multi-operation tool
      history.py                 history(action="undo"|"redo")
tests/
  conftest.py                    autouse fixture that resets the store singleton
  test_store.py
  test_helpers.py
  test_import_export.py
  test_inspect.py
  test_transform.py
  test_edit.py
  test_xlsx_edit.py
  test_batch.py
  test_history.py
```

---

## Architecture: the store singleton

`store.py` owns a **module-level singleton** of type `TableStore`. Access always goes through accessor functions so tests and `batch` can swap in a fresh instance:

```python
def get_store() -> TableStore: ...   # returns the live instance
def set_store(new: TableStore) -> None: ...  # swaps the singleton
```

**Every tool must call `get_store()` at invocation time.** Do not capture a reference at import time.

```python
# CORRECT
from data_mcp.store import get_store as _get_store
df = _get_store().get_table("sales")

# WRONG — stale after set_store() is called
from data_mcp.store import _store
df = _store.get_table("sales")
```

---

## The `TableStore` class (store.py)

| Method | Purpose |
|---|---|
| `add_table(name, df)` | Register (or overwrite) a DataFrame; history-tracked |
| `get_table(name) → pd.DataFrame` | Retrieve by name; raises `KeyError` if missing |
| `list_tables() → list[str]` | All registered names |
| `remove_table(name) → bool` | Drop a table; returns False if not found |
| `rename_table(old, new) → bool` | Rename in-place |
| `update_table(name, df)` | Replace a table's DataFrame (history-tracked) |
| `has_table(name) → bool` | Non-raising existence check |
| `undo() → bool` | Revert last mutation; returns False if stack empty |
| `redo() → bool` | Re-apply last undone mutation |

Every mutating method calls `_push_history()` first, enabling undo/redo up to 50 steps.

---

## Adding a new tool

1. Pick the right sub-module under `src/data_mcp/tools/` or create a new one.
2. Decorate the function with `@mcp.tool` (import `mcp` from `data_mcp.server`).
3. Import `get_store` from `data_mcp.store` — call it at invocation time, never at import time.
4. Return `table_response(df, "message")` or `text_response("message")` from `data_mcp._helpers`.
5. If you add a new sub-module, import it in `src/data_mcp/tools/__init__.py`.
6. Add the new tool name to `_dispatch` in `batch.py`.
7. Update the `INSTRUCTIONS` string in `server.py`.

Minimal template:

```python
from fastmcp.utilities.types import ContentBlock
from data_mcp._helpers import table_response
from data_mcp.store import get_store as _get_store
from data_mcp.server import mcp

@mcp.tool
def my_tool(table_name: str, param: str) -> list[ContentBlock]:
    """One-line description shown to the agent."""
    df = _get_store().get_table(table_name)
    # ... transform df ...
    _get_store().add_table(table_name, df)
    return table_response(df, f"Done: {param}.")
```

---

## Tool inventory (24 tools)

### Import / export (`import_export.py`)

| Tool | Signature | Notes |
|---|---|---|
| `import_table` | `(file_path, table_name=None, sheet_name=None, sep=",", header=0, encoding="utf-8")` | Auto-detects CSV vs XLSX from extension; `sheet_name` for Excel |
| `export_table` | `(table_names, file_path, sheet_name="Sheet1", index=False, sep=",", encoding="utf-8")` | str → single table; list → multi-sheet XLSX; auto-detects format |

### Inspection (`inspect.py`)

| Tool | Signature | Notes |
|---|---|---|
| `list_tables()` | `()` | Names, shapes, dtypes of all loaded tables |
| `info` | `(table_name, detail="schema")` | `detail` ∈ `"schema"` / `"shape"` / `"describe"` / `"all"` |
| `preview` | `(table_name, mode="head", n=10)` | `mode` ∈ `"head"` / `"tail"` / `"sample"` |
| `value_counts` | `(table_name, column)` | Frequency table for a column |

### Transform (`transform.py`)

| Tool | Notes |
|---|---|
| `filter_rows(table_name, query, result_table=None)` | `df.query()` |
| `sort_table(table_name, by, ascending=True, result_table=None)` | |
| `select_columns(table_name, columns, exclude=False, result_table=None)` | `exclude=True` drops the listed columns instead of keeping them |
| `rename_columns(table_name, mapping)` | Dict `{old: new}` |
| `add_column(table_name, column_name, expression)` | `df.eval()` |
| `drop_duplicates(table_name, subset=None, keep="first")` | |
| `handle_na(table_name, action="drop", subset=None, value=None, method=None, column=None)` | `action` ∈ `"drop"` / `"fill"` |
| `set_dtypes(table_name, dtypes)` | Dict `{col: dtype_str}` |
| `combine_tables(table_names, mode="concat", result_table=None, on=None, how="inner", axis=0)` | `mode` ∈ `"concat"` / `"merge"` |
| `group_by(table_name, by, agg, result_table=None)` | Dict `{col: func}` |
| `reshape(table_name, mode, result_table=None, ...)` | `mode` ∈ `"pivot"` / `"melt"` / `"transpose"` |

### Edit (`edit.py`)

| Tool | Notes |
|---|---|
| `update_cells(table_name, updates)` | List of `{row, column, value}` dicts; use a single-element list for one cell |
| `edit_rows(table_name, action, ...)` | `action` ∈ `"insert"` / `"delete"` / `"replace"` |
| `apply_formula(table_name, column, expression)` | `col` bound to the Series |

### XLSX sheet operations (`xlsx_edit.py`)

| Tool | Notes |
|---|---|
| `write_sheet(table_name, file_path, sheet_name, if_sheet_exists="replace")` | Writes one sheet without touching others |
| `manage_sheets(file_path, action="list", sheet_name=None, new_name=None, target_sheet=None)` | `action` ∈ `"list"` / `"delete"` / `"rename"` / `"copy"` |

### Batch (`batch.py`)

| Tool | Signature | Notes |
|---|---|---|
| `batch` | `(calls: list[dict])` | Execute multiple operations in one round-trip |

Each element of `calls` is `{"tool": "<name>", "args": {...}}`.

### History (`history.py`)

| Tool | Notes |
|---|---|
| `history(action)` | `action` ∈ `"undo"/"redo"` — up to 50 steps |

---

## `_helpers.py` — shared response builders

| Function | Purpose |
|---|---|
| `table_response(df, message="", max_rows=100)` | DataFrame → Markdown `TextContent` block |
| `text_response(message)` | Plain text `TextContent` block |
| `tables_list_response()` | Summary of all tables in the store |

---

## Key invariants to maintain

1. **Every tool returns a response.** Use `table_response()` or `text_response()` — never return `None`.
2. **Every mutation is history-tracked.** `TableStore` mutating methods call `_push_history()`. New methods must do the same.
3. **`get_store()` — always, everywhere.** No module-level or import-time references to the store object.
4. **Tool registration is by import side-effect.** `@mcp.tool` on the function is sufficient — just make sure the module is imported in `tools/__init__.py`.
5. **`batch._dispatch` must include every callable tool.** After adding a new tool, add it to the `_tool_map` dict in `batch.py`.

---

## Running and testing

```sh
# Run the MCP server (stdio transport)
PYTHONPATH=src python main.py

# Quick sanity check — counts registered tools
PYTHONPATH=src python -c "
import asyncio, data_mcp
tools = asyncio.run(data_mcp.mcp.list_tools())
print(len(tools), 'tools:', sorted(t.name for t in tools))
"

# Run the test suite
pytest
```

Dependencies: Python ≥ 3.14, pandas, openpyxl, xlsxwriter, tabulate, fastmcp.
