"""
API key settings service for the EREBUS presentation layer.

This service provides controlled read/write access to API credentials stored in
the SQLite database. It is intended for graphical settings pages where users can
save tokens used by optional API-based modules.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


class ApiKeySettingsService:
    """
    Service used to manage API credentials from the graphical interface.
    """

    API_CREDENTIALS_SCHEMA = """
        CREATE TABLE IF NOT EXISTS api_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL,
            api_key TEXT NOT NULL,
            extra TEXT,
            description TEXT,
            enabled INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(provider, api_key)
        );
    """

    def __init__(self, database_path: Path | None = None):
        """
        Initializes the API key settings service.

        Args:
            database_path: Optional custom SQLite database path.
        """
        self.database_path = database_path or self._get_default_database_path()
        self._ensure_database_ready()

    def _get_default_database_path(self) -> Path:
        """
        Gets the default EREBUS SQLite database path.

        Returns:
            Path: Default database path.
        """
        app_root = Path(__file__).resolve().parents[2]
        return app_root / "persistence" / "erebus.db"

    def _ensure_database_ready(self) -> None:
        """
        Ensures the database file and API credentials table exist.
        """
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as conn:
            conn.executescript(self.API_CREDENTIALS_SCHEMA)
            conn.commit()

    def get_api_key(self, provider: str) -> str:
        """
        Gets the stored API key for a provider.

        Args:
            provider: API provider name.

        Returns:
            str: Stored API key or an empty string.
        """
        normalized_provider = self._normalize_provider(provider)

        if not normalized_provider:
            return ""

        query = """
            SELECT api_key
            FROM api_credentials
            WHERE provider = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1;
        """

        with self._connect() as conn:
            row = conn.execute(query, (normalized_provider,)).fetchone()

        if not row:
            return ""

        return row["api_key"] or ""

    def get_enabled_api_key(self, provider: str) -> str:
        """
        Gets the stored API key for a provider.

        This method is kept as a readable alias for modules that conceptually ask
        for the key that should be used during execution. Since only one key per
        provider is stored, it returns the same value as get_api_key.

        Args:
            provider: API provider name.

        Returns:
            str: Stored API key or an empty string.
        """
        return self.get_api_key(provider)

    def save_api_key(
        self,
        provider: str,
        api_key: str,
        description: str | None = None,
    ) -> None:
        """
        Saves an API key for a provider.

        Any previous key for the same provider is deleted before inserting the
        new one. This keeps the database clean and ensures that there is only one
        stored key per provider.

        Args:
            provider: API provider name.
            api_key: API key to save.
            description: Optional credential description.

        Raises:
            ValueError: If the provider or API key is empty.
        """
        normalized_provider = self._normalize_provider(provider)
        normalized_api_key = self._normalize_api_key(api_key)

        if not normalized_provider:
            raise ValueError("Provider cannot be empty.")

        if not normalized_api_key:
            raise ValueError("API key cannot be empty.")

        with self._connect() as conn:
            conn.execute(
                """
                DELETE FROM api_credentials
                WHERE provider = ?;
                """,
                (normalized_provider,),
            )

            conn.execute(
                """
                INSERT INTO api_credentials (
                    provider,
                    api_key,
                    description,
                    enabled
                )
                VALUES (?, ?, ?, 1);
                """,
                (
                    normalized_provider,
                    normalized_api_key,
                    description,
                ),
            )

            conn.commit()

    def delete_api_key(self, provider: str) -> None:
        """
        Deletes the stored API key for a provider.

        Args:
            provider: API provider name.
        """
        normalized_provider = self._normalize_provider(provider)

        if not normalized_provider:
            return

        with self._connect() as conn:
            conn.execute(
                """
                DELETE FROM api_credentials
                WHERE provider = ?;
                """,
                (normalized_provider,),
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        """
        Opens a SQLite connection configured for row dictionaries.

        Returns:
            sqlite3.Connection: SQLite connection.
        """
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _normalize_provider(self, provider: str) -> str:
        """
        Normalizes a provider name before using it in the database.

        Args:
            provider: Raw provider name.

        Returns:
            str: Normalized provider name.
        """
        if provider is None:
            return ""

        return str(provider).strip().lower()

    def _normalize_api_key(self, api_key: str) -> str:
        """
        Normalizes an API key before storing it.

        Args:
            api_key: Raw API key.

        Returns:
            str: Normalized API key.
        """
        if api_key is None:
            return ""

        return str(api_key).strip()