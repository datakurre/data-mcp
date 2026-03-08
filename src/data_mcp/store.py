"""In-memory table store for data-mcp."""

from __future__ import annotations

import copy
from typing import Optional

import pandas as pd

_MAX_HISTORY = 50


class TableStore:
    """Holds a dict of named DataFrames with undo/redo history."""

    def __init__(self) -> None:
        self._tables: dict[str, pd.DataFrame] = {}
        self._undo_stack: list[dict[str, pd.DataFrame]] = []
        self._redo_stack: list[dict[str, pd.DataFrame]] = []

    # ------------------------------------------------------------------
    # Internal history management
    # ------------------------------------------------------------------

    def _push_history(self) -> None:
        """Snapshot current state onto the undo stack."""
        self._undo_stack.append(copy.deepcopy(self._tables))
        if len(self._undo_stack) > _MAX_HISTORY:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self) -> bool:
        """Revert to the previous state. Returns True on success."""
        if not self._undo_stack:
            return False
        self._redo_stack.append(copy.deepcopy(self._tables))
        self._tables = self._undo_stack.pop()
        return True

    def redo(self) -> bool:
        """Re-apply the last undone state. Returns True on success."""
        if not self._redo_stack:
            return False
        self._undo_stack.append(copy.deepcopy(self._tables))
        self._tables = self._redo_stack.pop()
        return True

    # ------------------------------------------------------------------
    # Table CRUD
    # ------------------------------------------------------------------

    def add_table(self, name: str, df: pd.DataFrame) -> None:
        """Register a DataFrame under *name*."""
        self._push_history()
        self._tables[name] = df.copy()

    def get_table(self, name: str) -> pd.DataFrame:
        """Retrieve a DataFrame by name. Raises KeyError if not found."""
        if name not in self._tables:
            raise KeyError(f"Table '{name}' not found. Available: {self.list_tables()}")
        return self._tables[name]

    def list_tables(self) -> list[str]:
        """Return the names of all registered tables."""
        return list(self._tables.keys())

    def remove_table(self, name: str) -> bool:
        """Drop a table by name. Returns True on success."""
        if name not in self._tables:
            return False
        self._push_history()
        del self._tables[name]
        return True

    def rename_table(self, old: str, new: str) -> bool:
        """Rename a table. Returns True on success."""
        if old not in self._tables:
            return False
        self._push_history()
        self._tables[new] = self._tables.pop(old)
        return True

    def update_table(self, name: str, df: pd.DataFrame) -> None:
        """Replace an existing table's DataFrame (history-tracked)."""
        self._push_history()
        self._tables[name] = df.copy()

    def has_table(self, name: str) -> bool:
        return name in self._tables


# ------------------------------------------------------------------
# Singleton accessors
# ------------------------------------------------------------------

_store: TableStore = TableStore()


def get_store() -> TableStore:
    """Return the live global TableStore instance."""
    return _store


def set_store(new: TableStore) -> None:
    """Swap in a new TableStore (used by tests and reset operations)."""
    global _store
    _store = new
