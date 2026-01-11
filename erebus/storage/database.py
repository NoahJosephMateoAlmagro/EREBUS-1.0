import sqlite3


class Database:
    def __init__(self, path="erebus.db"):
        self.conn = sqlite3.connect(path)
        self.create_db()

    # -------------------------------------------------
    # Creación de tablas
    # -------------------------------------------------

    def create_db(self):
        cursor = self.conn.cursor()

        # ------------------------
        # Ejecuciones
        # ------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS executions (
            id TEXT PRIMARY KEY,
            target TEXT,
            start_time TEXT,
            end_time TEXT,
            status TEXT
        )
        """)

        # ------------------------
        # Dominios descubiertos
        # ------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS domain_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT,
            domain TEXT,
            source TEXT,
            status TEXT,
            UNIQUE (execution_id, domain)
        )
        """)

        # ------------------------
        # Dominios resueltos (DNS)
        # ------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS resolved_domain_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT,
            domain TEXT,
            ip TEXT,
            source TEXT,
            UNIQUE (execution_id, domain, ip)
        )
        """)

        # ------------------------
        # WHOIS
        # ------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS whois_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT,
            domain TEXT,
            registrar TEXT,
            creation_date TEXT,
            expiration_date TEXT,
            updated_date TEXT,
            name_servers TEXT,
            status TEXT,
            emails TEXT,
            raw_text TEXT
        )
        """)

        # ------------------------
        # Emails (UNIFICADOS)
        # ------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT,
            email TEXT,
            domain TEXT,
            technique TEXT,
            source TEXT,
            context TEXT,
            UNIQUE (execution_id, email)
        )
        """)

        # ------------------------
        # Resultados del crawler (debug / trazabilidad)
        # ------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crawler_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT,
            url TEXT,
            emails TEXT,
            links TEXT,
            scripts TEXT
        )
        """)

        # ------------------------
        # Resultados JS (debug / trazabilidad)
        # ------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS js_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT,
            script_url TEXT,
            emails TEXT,
            urls TEXT
        )
        """)

        # ------------------------
        # Credenciales expuestas
        # ------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS credential_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT,
            type TEXT,
            value TEXT,
            technique TEXT,
            source TEXT,
            context TEXT,
            UNIQUE (execution_id, type, value)
        )
        """)

        # ------------------------
        # Métricas resumen
        # ------------------------
        cursor.execute("""CREATE TABLE IF NOT EXISTS execution_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT,
            metric TEXT,       
            value REAL
        )""")

        self.conn.commit()

    # -------------------------------------------------
    # Limpieza completa (para pruebas)
    # -------------------------------------------------

    def clear_all(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM executions")
        cursor.execute("DELETE FROM domain_results")
        cursor.execute("DELETE FROM resolved_domain_results")
        cursor.execute("DELETE FROM whois_results")
        cursor.execute("DELETE FROM email_results")
        cursor.execute("DELETE FROM crawler_results")
        cursor.execute("DELETE FROM js_results")
        cursor.execute("DELETE FROM credential_results")
        cursor.execute("DELETE FROM execution_metrics")
        self.conn.commit()

    # -------------------------------------------------
    # Ejecuciones
    # -------------------------------------------------

    def insert_execution(self, execution):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO executions (id, target, start_time, end_time, status)
        VALUES (?, ?, ?, ?, ?)
        """, (
            execution.ID,
            execution.TARGET,
            execution.START.isoformat(),
            execution.END.isoformat() if execution.END else None,
            execution.STATUS
        ))
        self.conn.commit()
    def update_execution(self, execution):
        cursor = self.conn.cursor()
        cursor.execute("""
        UPDATE executions
        SET end_time = ?, status = ?
        WHERE id = ?
        """, (
            execution.END.isoformat() if execution.END else None,
            execution.STATUS,
            execution.ID
        ))
        self.conn.commit()

    # -------------------------------------------------
    # Dominios
    # -------------------------------------------------

    def insert_domain(self, execution_id, domain, source, status):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO domain_results
            (execution_id, domain, source, status)
            VALUES (?, ?, ?, ?)
        """, (execution_id, domain, source, status))
        self.conn.commit()
    def update_domain_status(self, execution_id, domain, status):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE domain_results
            SET status = ?
            WHERE execution_id = ? AND domain = ?
        """, (status, execution_id, domain))
        self.conn.commit()
    def insert_resolved_domain(self, execution_id, domain, ip, source):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO resolved_domain_results
        (execution_id, domain, ip, source)
        VALUES (?, ?, ?, ?)
        """, (execution_id, domain, ip, source))
        self.conn.commit()

    # -------------------------------------------------
    # WHOIS
    # -------------------------------------------------

    def insert_whois_result(self, execution_id, domain, data):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO whois_results (
            execution_id,
            domain,
            registrar,
            creation_date,
            expiration_date,
            updated_date,
            name_servers,
            status,
            emails,
            raw_text
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execution_id,
            domain,
            data.get("registrar"),
            data.get("creation_date"),
            data.get("expiration_date"),
            data.get("updated_date"),
            self._list_to_str(data.get("name_servers")),
            self._list_to_str(data.get("status")),
            self._list_to_str(data.get("emails")),
            data.get("raw_text")
        ))
        self.conn.commit()

    # -------------------------------------------------
    # Emails
    # -------------------------------------------------

    def insert_email(self, execution_id, email, domain, technique, source, context):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO email_results
        (execution_id, email, domain, technique, source, context)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (execution_id, email, domain, technique, source, context))
        self.conn.commit()

    # -------------------------------------------------
    # Crawler / JS (debug)
    # -------------------------------------------------

    def insert_crawler_result(self, execution_id, url, emails, links, scripts):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO crawler_results
        (execution_id, url, emails, links, scripts)
        VALUES (?, ?, ?, ?, ?)
        """, (
            execution_id,
            url,
            ",".join(emails),
            ",".join(links),
            ",".join(scripts)
        ))
        self.conn.commit()
    def insert_js_result(self, execution_id, script_url, emails, urls):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO js_results
        (execution_id, script_url, emails, urls)
        VALUES (?, ?, ?, ?)
        """, (
            execution_id,
            script_url,
            ",".join(emails),
            ",".join(urls)
        ))
        self.conn.commit()

    # -------------------------------------------------
    # Credenciales
    # -------------------------------------------------

    def insert_credential(self, execution_id, ctype, value, technique, source, context):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO credential_results
        (execution_id, type, value, technique, source, context)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (execution_id, ctype, value, technique, source, context))
        self.conn.commit()

    # -------------------------------------------------
    # Métricas resumen
    # -------------------------------------------------

    def insert_metric(self, execution_id, metric, value):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO execution_metrics (execution_id, metric, value)
            VALUES (?, ?, ?)
        """, (execution_id, metric, value))
        self.conn.commit()

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------
    def _list_to_str(self, value):
        if value is None:
            return None
        if isinstance(value, list):
            return ", ".join(str(v) for v in value)
        return str(value)
