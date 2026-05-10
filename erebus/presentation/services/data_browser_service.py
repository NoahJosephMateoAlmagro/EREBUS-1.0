"""
Data browser service for the EREBUS presentation layer.

This service provides read-only access to the SQLite database so the Data page
can inspect stored execution results without coupling the GUI to engine
repositories.
"""

import sqlite3
from pathlib import Path

from application.config import APP_CONFIG


class DataBrowserService:
    """
    Provides read-only database inspection helpers for the Data page.
    """

    DEFAULT_DB_PATH = Path("persistence") / "erebus.db"

    DOMAIN_FILTER_COLUMNS = {
        "domain",
        "target",
        "target_domain",
        "subdomain",
        "host",
        "hostname",
        "url",
        "source_url",
        "page_url",
        "email",
    }

    def __init__(self, database_path=None):
        """
        Initializes the service.

        Args:
            database_path: Optional explicit SQLite database path.
        """
        self.database_path = Path(database_path or self._resolve_database_path())

    def _resolve_database_path(self):
        """
        Resolves the SQLite database path from APP_CONFIG when available.

        Returns:
            Path: SQLite database path.
        """
        configured_path = (
            APP_CONFIG.get("database", {}).get("path")
            or APP_CONFIG.get("db", {}).get("path")
            or APP_CONFIG.get("persistence", {}).get("database_path")
        )

        if configured_path:
            return Path(configured_path)

        return self.DEFAULT_DB_PATH

    def database_exists(self):
        """
        Checks whether the configured database exists.

        Returns:
            bool: True if the database file exists.
        """
        return self.database_path.exists()

    def get_table_names(self):
        """
        Gets user-created SQLite table names.

        Returns:
            list[str]: Table names.
        """
        if not self.database_exists():
            return []

        query = """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
        """

        with self._connect() as conn:
            rows = conn.execute(query).fetchall()

        return [row["name"] for row in rows]

    def get_columns(self, table_name):
        """
        Gets the column names for a table.

        Args:
            table_name: SQLite table name.

        Returns:
            list[str]: Column names.
        """
        if not self.database_exists():
            return []

        safe_table_name = self._validate_identifier(table_name)

        with self._connect() as conn:
            rows = conn.execute(f"PRAGMA table_info({safe_table_name})").fetchall()

        return [row["name"] for row in rows]

    def get_rows(self, table_name, domain_filter="", limit=100):
        """
        Gets table rows, optionally filtered by domain.

        Args:
            table_name: SQLite table name.
            domain_filter: Domain text used to filter common domain columns.
            limit: Maximum number of rows.

        Returns:
            tuple[list[str], list[dict]]: Column names and row dictionaries.
        """
        if not self.database_exists():
            return [], []

        safe_table_name = self._validate_identifier(table_name)
        columns = self.get_columns(table_name)

        if not columns:
            return [], []

        limit = self._sanitize_limit(limit)
        filter_columns = self._get_existing_filter_columns(columns)

        params = []
        where_sql = ""

        if domain_filter and filter_columns:
            where_parts = []

            for column in filter_columns:
                safe_column = self._validate_identifier(column)
                where_parts.append(f"CAST({safe_column} AS TEXT) LIKE ?")
                params.append(f"%{domain_filter}%")

            where_sql = "WHERE " + " OR ".join(where_parts)

        query = f"""
            SELECT *
            FROM {safe_table_name}
            {where_sql}
            LIMIT ?;
        """

        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return columns, [dict(row) for row in rows]

    def count_rows(self, table_name, domain_filter=""):
        """
        Counts table rows, optionally filtered by domain.

        Args:
            table_name: SQLite table name.
            domain_filter: Domain text used to filter common domain columns.

        Returns:
            int: Matching row count.
        """
        if not self.database_exists():
            return 0

        safe_table_name = self._validate_identifier(table_name)
        columns = self.get_columns(table_name)

        if not columns:
            return 0

        filter_columns = self._get_existing_filter_columns(columns)

        params = []
        where_sql = ""

        if domain_filter and filter_columns:
            where_parts = []

            for column in filter_columns:
                safe_column = self._validate_identifier(column)
                where_parts.append(f"CAST({safe_column} AS TEXT) LIKE ?")
                params.append(f"%{domain_filter}%")

            where_sql = "WHERE " + " OR ".join(where_parts)

        query = f"""
            SELECT COUNT(*) AS total
            FROM {safe_table_name}
            {where_sql};
        """

        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()

        return int(row["total"]) if row else 0

    def _get_existing_filter_columns(self, columns):
        """
        Gets table columns that can be used for domain filtering.

        Args:
            columns: Existing table columns.

        Returns:
            list[str]: Matching filter columns.
        """
        return [
            column
            for column in columns
            if column.lower() in self.DOMAIN_FILTER_COLUMNS
            or "domain" in column.lower()
            or "url" in column.lower()
            or "host" in column.lower()
        ]

    def _connect(self):
        """
        Opens a read-only SQLite connection.

        Returns:
            sqlite3.Connection: SQLite connection.
        """
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _validate_identifier(self, identifier):
        """
        Validates a SQLite identifier used in generated SQL.

        Args:
            identifier: Table or column name.

        Returns:
            str: Quoted safe identifier.

        Raises:
            ValueError: If the identifier is unsafe.
        """
        if not identifier:
            raise ValueError("Empty database identifier.")

        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")

        if any(char not in allowed for char in identifier):
            raise ValueError(f"Unsafe database identifier: {identifier}")

        return f'"{identifier}"'

    def _sanitize_limit(self, limit):
        """
        Sanitizes the row limit.

        Args:
            limit: Raw limit.

        Returns:
            int: Safe row limit.
        """
        try:
            value = int(limit)
        except Exception:
            value = 100

        return max(10, min(value, 1000))