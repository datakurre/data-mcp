# data-mcp

An MCP server for importing, manipulating, and exporting tabular data (CSV/XLSX) using pandas. Tables live in a persistent in-memory store across tool calls. Every tool returns a Markdown-formatted text response for easy inspection.

## Features

- Import CSV and XLSX files into named in-memory tables
- Inspect tables: `head`, `tail`, `describe`, `schema`, `shape`, `sample`, `value_counts`
- Transform data: filter, sort, select columns, rename, add columns, merge, group-by, pivot, melt, transpose, and more
- Edit cells and rows: `update_cell`, `insert_row`, `delete_rows`, `apply_formula`, etc.
- XLSX sheet management: list, read, write, delete, rename, and copy sheets without touching the rest of the workbook
- Undo/redo up to 50 steps
- `batch` tool for executing multiple operations in a single round-trip
- Export to CSV or XLSX (single or multi-sheet workbook)

## Installation

```sh
pip install -e .
```

Requires Python ≥ 3.14 and the Cairo system library is **not** needed (pure pandas/openpyxl).

## Running the server

```sh
# stdio transport (used by MCP hosts)
python main.py

# or via the installed script
data-mcp
```

## Quick example

```python
# Via an MCP client or batch tool:
batch(calls=[
    {"tool": "import_csv", "args": {"file_path": "sales.csv", "table_name": "sales"}},
    {"tool": "filter_rows", "args": {"table_name": "sales", "query": "revenue > 1000", "result_table": "big_sales"}},
    {"tool": "group_by",    "args": {"table_name": "big_sales", "by": "region", "agg": {"revenue": "sum"}}},
    {"tool": "export_csv",  "args": {"table_name": "big_sales", "file_path": "big_sales.csv"}}
])
```

## Tool reference (43 tools)

### Import / export
| Tool | Description |
|---|---|
| `import_csv(file_path, table_name=None, ...)` | Import a CSV into the store |
| `import_xlsx(file_path, table_name=None, sheet_name=0)` | Import an XLSX sheet |
| `export_csv(table_name, file_path, ...)` | Write a table to CSV |
| `export_xlsx(table_name, file_path, sheet_name="Sheet1")` | Write a table to XLSX |
| `export_multi_xlsx(table_names, file_path)` | Write multiple tables as sheets in one workbook |

### Inspection
| Tool | Description |
|---|---|
| `list_tables()` | Names, shapes, dtypes of all loaded tables |
| `describe_table(table_name)` | Summary statistics |
| `head(table_name, n=10)` | First N rows |
| `tail(table_name, n=10)` | Last N rows |
| `schema(table_name)` | Column names, dtypes, null counts |
| `shape(table_name)` | Row × column count |
| `sample(table_name, n=5)` | Random sample |
| `value_counts(table_name, column)` | Frequency table |

### Transform
| Tool | Description |
|---|---|
| `filter_rows(table_name, query, result_table=None)` | Pandas query string |
| `sort_table(table_name, by, ascending=True, result_table=None)` | |
| `select_columns(table_name, columns, result_table=None)` | |
| `drop_columns(table_name, columns)` | |
| `rename_columns(table_name, mapping)` | `{old: new}` dict |
| `add_column(table_name, column_name, expression)` | `df.eval()` expression |
| `drop_duplicates(table_name, subset=None, keep="first")` | |
| `fill_na(table_name, value=None, method=None, column=None)` | |
| `drop_na(table_name, subset=None)` | |
| `set_dtypes(table_name, dtypes)` | `{col: dtype}` dict |
| `merge_tables(left, right, on, how="inner", result_table=None)` | `pd.merge()` |
| `concat_tables(table_names, result_table=None, axis=0)` | `pd.concat()` |
| `group_by(table_name, by, agg, result_table=None)` | `{col: func}` aggregation dict |
| `pivot_table(table_name, index, columns, values, aggfunc, result_table=None)` | |
| `melt(table_name, id_vars, value_vars=None, result_table=None)` | Wide → long |
| `transpose(table_name, result_table=None)` | |

### Edit
| Tool | Description |
|---|---|
| `update_cell(table_name, row, column, value)` | Set a single cell |
| `update_cells(table_name, updates)` | Batch cell updates |
| `insert_row(table_name, row_data, index=None)` | Insert a row |
| `delete_rows(table_name, indices)` | Delete rows by position |
| `replace_values(table_name, column, to_replace, value)` | |
| `apply_formula(table_name, column, expression)` | `col` = column Series |

### XLSX sheet management
| Tool | Description |
|---|---|
| `list_sheets(file_path)` | Sheet names in a workbook |
| `read_sheet(file_path, sheet_name, table_name=None)` | Read sheet → store |
| `write_sheet(table_name, file_path, sheet_name, if_sheet_exists="replace")` | Update one sheet |
| `delete_sheet(file_path, sheet_name)` | |
| `rename_sheet(file_path, old_name, new_name)` | |
| `copy_sheet(file_path, source_sheet, target_sheet)` | |

### Utility
| Tool | Description |
|---|---|
| `batch(calls)` | Run multiple tools in one call |
| `history(action)` | `"undo"` or `"redo"` |

## Development

```sh
# Run tests
pytest

# Check all tools register
PYTHONPATH=src python -c "
import asyncio, data_mcp
tools = asyncio.run(data_mcp.mcp.list_tools())
print(len(tools), 'tools registered')
"
```

See [AGENTS.md](AGENTS.md) for the full developer guide.
