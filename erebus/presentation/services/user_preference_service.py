"""
User preference persistence service for the EREBUS presentation layer.

This module provides a small JSON-based persistence layer for user-facing
preferences related to the execution screen. It is intentionally isolated from
the execution engine and from the main results database.

The service stores only stable UI preferences, such as:
- last target domain
- execution form values
- enabled modules
- runtime configuration overrides

It does not store transient runtime state such as progress, console output or
currently running modules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class UserPreferencesService:
    """
    JSON-based persistence service for user preferences.

    The service loads and saves a dictionary that represents stable user
    preferences for the presentation layer.
    """

    def __init__(self, base_dir: Path | None = None):
        """
        Initializes the user preference service.

        Args:
            base_dir: Optional base directory where the JSON file will be stored.
                If omitted, the file is stored inside the presentation package.
        """
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent.parent

        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "user_data"
        self.file_path = self.data_dir / "preferences.json"

    def load_preferences(self) -> dict[str, Any]:
        """
        Loads persisted user preferences from disk.

        Returns:
            dict[str, Any]: Loaded preference dictionary. If the file does not
            exist or cannot be parsed, an empty dictionary is returned.
        """
        try:
            if not self.file_path.exists():
                return {}

            raw = self.file_path.read_text(encoding="utf-8").strip()
            if not raw:
                return {}

            data = json.loads(raw)

            if not isinstance(data, dict):
                return {}

            return data

        except Exception:
            return {}

    def save_preferences(self, data: dict[str, Any]) -> None:
        """
        Saves user preferences to disk.

        Args:
            data: Preference dictionary to store.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)

        serialized = json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )

        self.file_path.write_text(serialized, encoding="utf-8")