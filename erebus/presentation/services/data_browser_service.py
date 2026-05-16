"""
Data browser service for the EREBUS presentation layer.

This service provides read-only access to the SQLite database used by EREBUS.
It is intended for the Data page, where stored results can be inspected without
modifying the database.
"""

from __future__ import annotations

import math
import sqlite3
from pathlib import Path


class DataBrowserService:
    """
    Read-only helper used to inspect EREBUS database tables.

    This service exposes paginated read operations only. The Data page should
    never load a full table at once because large result sets can make the
    graphical interface slow and unresponsive.
    """

    DEFAULT_PAGE = 1
    DEFAULT_PAGE_SIZE = 100
    MIN_PAGE_SIZE = 25
    MAX_PAGE_SIZE = 200

    TABLE_ORDER = [
        "executions",
        "domain_results",
        "resolved_domain_results",
        "dns_observations",
        "http_headers",
        "whois_results",
        "email_results",
        "crawler_results",
        "js_results",
        "credential_results",
        "nmap_results",
    ]

    HIDDEN_TABLES = {
        "api_credentials",
        "sqlite_sequence",
    }

    SENSITIVE_COLUMNS = {
        "api_key",
        "password",
        "secret",
        "token",
    }

    def __init__(self, database_path: Path | None = None):
        """
        Initializes the database browser service.

        Args:
            database_path: Optional custom SQLite database path.
        """
        self.database_path = database_path or self._get_default_database_path()

    def _get_default_database_path(self) -> Path:
        """
        Gets the default EREBUS SQLite database path.

        The path mirrors the one used by persistence.database.Database.

        Returns:
            Path: Default database path.
        """
        app_root = Path(__file__).resolve().parents[2]
        return app_root / "persistence" / "erebus.db"

    def database_exists(self) -> bool:
        """
        Checks whether the configured database file exists.

        Returns:
            bool: True if the database exists, False otherwise.
        """
        return self.database_path.exists()

    def get_table_names(self) -> list[str]:
        """
        Gets visible user-defined database tables.

        Returns:
            list[str]: Visible table names.
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

        discovered_tables = [
            row["name"]
            for row in rows
            if row["name"] not in self.HIDDEN_TABLES
        ]

        ordered_tables = [
            table_name
            for table_name in self.TABLE_ORDER
            if table_name in discovered_tables
        ]

        extra_tables = sorted(
            table_name
            for table_name in discovered_tables
            if table_name not in ordered_tables
        )

        return ordered_tables + extra_tables

    def get_table_columns(self, table_name: str) -> list[str]:
        """
        Gets the safe display columns of a database table.

        Args:
            table_name: Database table name.

        Returns:
            list[str]: Column names.
        """
        if not self._is_visible_table(table_name):
            return []

        safe_table_name = self._quote_identifier(table_name)

        with self._connect() as conn:
            rows = conn.execute(f"PRAGMA table_info({safe_table_name})").fetchall()

        return [
            row["name"]
            for row in rows
            if not self._is_sensitive_column(row["name"])
        ]

    def count_table_rows(
        self,
        table_name: str,
        execution_filter: str = "",
    ) -> int:
        """
        Counts rows from a table using an optional execution identifier filter.

        Args:
            table_name: Database table name.
            execution_filter: Optional text matched against execution identifiers.

        Returns:
            int: Number of matching rows.
        """
        if not self.database_exists():
            return 0

        if not self._is_visible_table(table_name):
            return 0

        columns = self.get_table_columns(table_name)

        if not columns:
            return 0

        safe_table_name = self._quote_identifier(table_name)

        query = f"""
            SELECT COUNT(*) AS total
            FROM {safe_table_name}
        """

        params = []
        where_sql = self._build_execution_filter_sql(
            table_name=table_name,
            columns=columns,
            execution_filter=execution_filter,
            params=params,
        )

        if where_sql:
            query += f" WHERE {where_sql}"

        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()

        if not row:
            return 0

        return int(row["total"])

    def fetch_table_page(
        self,
        table_name: str,
        execution_filter: str = "",
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> dict:
        """
        Fetches a paginated table page using an optional execution identifier filter.

        Args:
            table_name: Database table name.
            execution_filter: Optional text matched against execution identifiers.
            page: 1-based page number.
            page_size: Number of rows per page.

        Returns:
            dict: Page data with columns, rows and pagination metadata.
        """
        empty_result = self._build_empty_page_result(
            table_name=table_name,
            page=page,
            page_size=page_size,
            execution_filter=execution_filter,
        )

        if not self.database_exists():
            return empty_result

        if not self._is_visible_table(table_name):
            return empty_result

        columns = self.get_table_columns(table_name)

        if not columns:
            return empty_result

        safe_page_size = self._sanitize_page_size(page_size)

        total_rows = self.count_table_rows(
            table_name=table_name,
            execution_filter=execution_filter,
        )

        total_pages = self._calculate_total_pages(total_rows, safe_page_size)
        safe_page = self._sanitize_page(page, total_pages)

        offset = (safe_page - 1) * safe_page_size

        safe_table_name = self._quote_identifier(table_name)
        select_columns = ", ".join(
            self._quote_identifier(column)
            for column in columns
        )

        query = f"""
            SELECT {select_columns}
            FROM {safe_table_name}
        """

        params = []
        where_sql = self._build_execution_filter_sql(
            table_name=table_name,
            columns=columns,
            execution_filter=execution_filter,
            params=params,
        )

        if where_sql:
            query += f" WHERE {where_sql}"

        query += self._build_default_order_sql(table_name)
        query += " LIMIT ? OFFSET ?"
        params.extend([safe_page_size, offset])

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return {
            "table_name": table_name,
            "columns": columns,
            "rows": [dict(row) for row in rows],
            "page": safe_page,
            "page_size": safe_page_size,
            "total_rows": total_rows,
            "total_pages": total_pages,
            "has_previous": safe_page > 1,
            "has_next": safe_page < total_pages,
            "execution_filter": execution_filter.strip(),
        }

    def _build_empty_page_result(
        self,
        table_name: str,
        page: int,
        page_size: int,
        execution_filter: str = "",
    ) -> dict:
        """
        Builds an empty paginated response.

        Args:
            table_name: Database table name.
            page: Requested page.
            page_size: Requested page size.
            execution_filter: Optional execution identifier filter.

        Returns:
            dict: Empty page response.
        """
        safe_page_size = self._sanitize_page_size(page_size)
        safe_page = max(1, int(page)) if self._can_be_int(page) else self.DEFAULT_PAGE

        return {
            "table_name": table_name,
            "columns": [],
            "rows": [],
            "page": safe_page,
            "page_size": safe_page_size,
            "total_rows": 0,
            "total_pages": 1,
            "has_previous": False,
            "has_next": False,
            "execution_filter": execution_filter.strip(),
        }

    def _build_execution_filter_sql(
        self,
        table_name: str,
        columns: list[str],
        execution_filter: str,
        params: list,
    ) -> str:
        """
        Builds the WHERE SQL used by the execution identifier filter.

        The filter is intentionally based on execution identifiers. New EREBUS
        execution IDs are expected to include target and timestamp information,
        for example: domain_es_2026_05_10_17_04_27.

        This means filtering by domain, date or hour works because those values
        are part of the execution ID itself.

        Args:
            table_name: Database table name.
            columns: Available display columns.
            execution_filter: Filter text entered by the user.
            params: Query parameter list to be extended.

        Returns:
            str: SQL WHERE fragment without the WHERE keyword.
        """
        execution_filter = execution_filter.strip()

        if not execution_filter:
            return ""

        like_value = f"%{execution_filter}%"

        if table_name == "executions":
            if "id" not in columns:
                return ""

            params.append(like_value)
            return 'CAST("id" AS TEXT) LIKE ?'

        if "execution_id" in columns:
            params.append(like_value)
            return 'CAST("execution_id" AS TEXT) LIKE ?'

        return ""

    def _build_default_order_sql(self, table_name: str) -> str:
        """
        Builds a simple ORDER BY clause for readable browsing.

        Args:
            table_name: Database table name.

        Returns:
            str: ORDER BY SQL fragment.
        """
        if table_name == "executions":
            return " ORDER BY start_time DESC"

        if table_name in {
            "domain_results",
            "resolved_domain_results",
            "dns_observations",
            "http_headers",
            "whois_results",
            "email_results",
            "crawler_results",
            "js_results",
            "credential_results",
            "nmap_results",
        }:
            return " ORDER BY id DESC"

        return ""

    def _connect(self) -> sqlite3.Connection:
        """
        Opens a SQLite read-only connection configured for row dictionaries.

        Returns:
            sqlite3.Connection: SQLite connection.
        """
        conn = sqlite3.connect(
            f"file:{self.database_path}?mode=ro",
            uri=True,
        )
        conn.row_factory = sqlite3.Row
        return conn

    def _sanitize_page_size(self, page_size: int) -> int:
        """
        Sanitizes a requested page size.

        Args:
            page_size: Requested page size.

        Returns:
            int: Safe page size.
        """
        try:
            value = int(page_size)
        except Exception:
            value = self.DEFAULT_PAGE_SIZE

        return max(self.MIN_PAGE_SIZE, min(value, self.MAX_PAGE_SIZE))

    def _sanitize_page(self, page: int, total_pages: int) -> int:
        """
        Sanitizes a requested page number.

        Args:
            page: Requested page number.
            total_pages: Total available pages.

        Returns:
            int: Safe page number.
        """
        try:
            value = int(page)
        except Exception:
            value = self.DEFAULT_PAGE

        total_pages = max(1, int(total_pages))
        return max(1, min(value, total_pages))

    def _calculate_total_pages(self, total_rows: int, page_size: int) -> int:
        """
        Calculates the number of pages for a result set.

        Args:
            total_rows: Total number of rows.
            page_size: Rows per page.

        Returns:
            int: Total pages.
        """
        if total_rows <= 0:
            return 1

        return max(1, math.ceil(total_rows / page_size))

    def _can_be_int(self, value) -> bool:
        """
        Checks whether a value can be converted to int.

        Args:
            value: Value to validate.

        Returns:
            bool: True if the value can be converted to int.
        """
        try:
            int(value)
            return True
        except Exception:
            return False

    def _is_visible_table(self, table_name: str) -> bool:
        """
        Checks whether a table can be displayed.

        Args:
            table_name: Table name.

        Returns:
            bool: True if the table is safe and visible.
        """
        if not self._is_safe_identifier(table_name):
            return False

        if table_name in self.HIDDEN_TABLES:
            return False

        return table_name in self.get_table_names()

    def _is_sensitive_column(self, column_name: str) -> bool:
        """
        Checks whether a column should be hidden from the Data page.

        Args:
            column_name: Column name.

        Returns:
            bool: True if the column is sensitive.
        """
        lowered = column_name.lower()

        return any(
            sensitive_name in lowered
            for sensitive_name in self.SENSITIVE_COLUMNS
        )

    def _quote_identifier(self, identifier: str) -> str:
        """
        Quotes a safe SQLite identifier.

        Args:
            identifier: Table or column name.

        Returns:
            str: Quoted identifier.

        Raises:
            ValueError: If the identifier is unsafe.
        """
        if not self._is_safe_identifier(identifier):
            raise ValueError(f"Unsafe database identifier: {identifier}")

        return f'"{identifier}"'

    def _is_safe_identifier(self, identifier: str) -> bool:
        """
        Validates a SQLite identifier before using it in generated SQL.

        SQLite query parameters cannot be used for table or column names, so
        identifiers must be validated manually.

        Args:
            identifier: Table or column name.

        Returns:
            bool: True if the identifier is safe.
        """
        if not identifier:
            return False

        return identifier.replace("_", "").isalnum()