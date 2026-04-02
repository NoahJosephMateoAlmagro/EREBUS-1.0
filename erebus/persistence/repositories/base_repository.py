class BaseRepository:
    """
    Base repository providing low-level database operations.

    This class centralizes common database access methods used by all repositories,
    including query execution and data retrieval.

    It assumes a valid SQLite connection and performs immediate commits on write operations.
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

        This method automatically commits the transaction after execution.

        Args:
            query: SQL query string
            params: Query parameters tuple
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()

    def _fetchone(self, query, params=()):
        """
        Executes a query and returns a single row.

        Args:
            query: SQL query string
            params: Query parameters tuple

        Returns:
            A single row or None if no result is found
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def _fetchall(self, query, params=()):
        """
        Executes a query and returns all matching rows.

        Args:
            query: SQL query string
            params: Query parameters tuple

        Returns:
            List of rows
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()