from pathlib import Path
import sqlite3
import os

from persistence.schema import SCHEMA_SQL
from shared.logger import Logger
from exceptions.exceptions import DatabaseError


class Database:
    """
    Database manager responsible for initializing and maintaining
    the SQLite database used by EREBUS.
    """

    def __init__(self):
        """
        Initializes database connection and ensures schema is created.
        """
        local_app_data = os.getenv("LOCALAPPDATA")

        if local_app_data:
            db_dir = Path(local_app_data) / "EREBUS" / "persistence"
        else:
            db_dir = Path.home() / ".erebus" / "persistence"

        db_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.db_path = db_dir / "erebus.db"

        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute("PRAGMA foreign_keys = ON;")
        except Exception as e:
            Logger.error(
                f"Database connection error: {e}",
                context=self.__class__.__name__
            )
            raise DatabaseError(f"Failed to connect to database: {self.db_path}") from e

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
            raise DatabaseError("Failed to initialize database schema") from e

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
            raise DatabaseError("Failed to clear database") from e

    # -------------------------------------------------
    # Connection management
    # -------------------------------------------------

    def close(self) -> None:
        """
        Closes database connection.
        """
        if self.conn:
            try:
                self.conn.close()
            except Exception as e:
                Logger.error(
                    f"Database close error: {e}",
                    context=self.__class__.__name__
                )
                raise DatabaseError("Failed to close database connection") from e