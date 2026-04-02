import json


class ApiRepository:
    """
    Repository responsible for retrieving external API credentials.

    """

    def __init__(self, conn):
        """
        Initializes the repository with a database connection.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn

    def get_provider_credentials(self, provider):
        """
        Retrieves active credentials for a given provider.
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT api_key, extra
            FROM api_credentials
            WHERE provider = ?
            AND enabled = 1
            LIMIT 1
        """, (provider,))

        row = cursor.fetchone()

        if not row:
            return None

        api_key, extra = row

        return {
            "api_key": api_key,
            "extra": json.loads(extra) if extra else {}
        }