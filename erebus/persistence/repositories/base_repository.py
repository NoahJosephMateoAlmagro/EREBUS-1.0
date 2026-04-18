import sqlite3
from exceptions.exceptions import DatabaseError


class BaseRepository:
    """
    Base repository providing low-level database operations.

    This class centralizes common database access methods used by all repositories,
    including query execution and data retrieval.

    It assumes a valid SQLite connection.
    Transaction control should be handled by the UnitOfWork.
    """

    def __init__(self, conn):
        """
        Initializes the repository with a database connection.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn

    def _execute(self, query, params=()):
        """
        Executes a write operation (INSERT, UPDATE, DELETE).

        Args:
            query: SQL query string
            params: Query parameters tuple

        Returns:
            sqlite3.Cursor: Cursor after execution
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor

        except sqlite3.IntegrityError as e:
            raise DatabaseError(str(e)) from e

        except sqlite3.OperationalError as e:
            raise DatabaseError(f"Operational DB error: {e}") from e

        except sqlite3.ProgrammingError as e:
            raise DatabaseError(f"Programming DB error: {e}") from e

        except sqlite3.DatabaseError as e:
            raise DatabaseError(f"Database error: {e}") from e

    def _fetchone(self, query, params=()):
        """
        Executes a query and returns a single row.

        Args:
            query: SQL query string
            params: Query parameters tuple

        Returns:
            A single row or None if no result is found
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()

        except sqlite3.OperationalError as e:
            raise DatabaseError(f"Operational DB error: {e}") from e

        except sqlite3.ProgrammingError as e:
            raise DatabaseError(f"Programming DB error: {e}") from e

        except sqlite3.DatabaseError as e:
            raise DatabaseError(f"Database error: {e}") from e

    def _fetchall(self, query, params=()):
        """
        Executes a query and returns all matching rows.

        Args:
            query: SQL query string
            params: Query parameters tuple

        Returns:
            List of rows
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

        except sqlite3.OperationalError as e:
            raise DatabaseError(f"Operational DB error: {e}") from e

        except sqlite3.ProgrammingError as e:
            raise DatabaseError(f"Programming DB error: {e}") from e

        except sqlite3.DatabaseError as e:
            raise DatabaseError(f"Database error: {e}") from e