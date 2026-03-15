from pathlib import Path
import shared.constants as C
from persistence.schema import SCHEMA_SQL
import sqlite3

class Database:
    def __init__(self):

        APP_ROOT = Path(__file__).resolve().parents[1]  # erebus/
        db_dir = APP_ROOT / "persistence"
        db_dir.mkdir(exist_ok=True)

        self.db_path = db_dir / "erebus.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON;")

        print(f"[DB] Using database at: {self.db_path.resolve()}")

        self.create_db()


    # -------------------------------------------------
    # Creación de tablas
    # -------------------------------------------------

    def create_db(self):
        cursor = self.conn.cursor()
        cursor.executescript(SCHEMA_SQL)
        self.conn.commit()

    # -------------------------------------------------
    # Limpieza completa (para pruebas)
    # -------------------------------------------------

    def clear_all(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM executions")
        cursor.execute("DELETE FROM domain_results")
        cursor.execute("DELETE FROM resolved_domain_results")
        cursor.execute("DELETE FROM dns_observations")
        cursor.execute("DELETE FROM whois_results")
        cursor.execute("DELETE FROM email_results")
        cursor.execute("DELETE FROM crawler_results")
        cursor.execute("DELETE FROM js_results")
        cursor.execute("DELETE FROM credential_results")
        cursor.execute("DELETE FROM execution_metrics")
        cursor.execute("DELETE FROM http_headers")
        cursor.execute("DELETE FROM nmap_results")
        self.conn.commit()


