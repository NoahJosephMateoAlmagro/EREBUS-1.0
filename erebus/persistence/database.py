from pathlib import Path
import sqlite3

from persistence.schema import SCHEMA_SQL
from shared.logger import Logger


class Database:
    """
    Database manager responsible for initializing and maintaining
    the SQLite database used by EREBUS.
    """

    def __init__(self):
        """
        Initializes database connection and ensures schema is created.
        """
        app_root = Path(__file__).resolve().parents[1]
        db_dir = app_root / "persistence"
        db_dir.mkdir(exist_ok=True)

        self.db_path = db_dir / "erebus.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON;")

        Logger.info(
            f"Using database at: {self.db_path.resolve()}",
            context=self.__class__.__name__
        )

        self._create_db()

    # -------------------------------------------------
    # Schema creation
    # -------------------------------------------------

    def _create_db(self) -> None:
        """
        Creates database schema if not already present.
        """
        try:
            cursor = self.conn.cursor()
            cursor.executescript(SCHEMA_SQL)
            self.conn.commit()

        except Exception as e:
            Logger.error(
                f"Database initialization error: {e}",
                context=self.__class__.__name__
            )
            raise

    # -------------------------------------------------
    # Cleanup (testing purposes)
    # -------------------------------------------------

    def clear_all(self) -> None:
        """
        Clears all execution-related data.

        Note:
            Uses cascade delete from executions table.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM executions")
            self.conn.commit()

            Logger.info(
                "Database cleared (all executions removed)",
                context=self.__class__.__name__
            )

        except Exception as e:
            Logger.error(
                f"Database cleanup error: {e}",
                context=self.__class__.__name__
            )
            raise

    # -------------------------------------------------
    # Connection management
    # -------------------------------------------------

    def close(self) -> None:
        """
        Closes database connection.
        """
        if self.conn:
            self.conn.close()