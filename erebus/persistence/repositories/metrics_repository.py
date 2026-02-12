from .base_repository import BaseRepository


class MetricsRepository(BaseRepository):

    def insert_metrics(self, execution_id: int):
        # ======================
        # EMAILS
        # ======================

        # Total emails
        self._execute("""
            INSERT INTO execution_metrics (execution_id, metric, value)
            SELECT ?, 'emails_total', COUNT(*)
            FROM email_results
            WHERE execution_id = ?
        """, (execution_id, execution_id))

        # Emails por técnica
        email_metrics = [
            ("emails_crawler_html", "crawler_html"),
            ("emails_js_static", "js_static"),
            ("emails_scraping_dom", "scraping_dom"),
            ("emails_scraping_json", "scraping_json"),
        ]

        for metric_name, technique in email_metrics:
            self._execute("""
                INSERT INTO execution_metrics (execution_id, metric, value)
                SELECT ?, ?, COUNT(*)
                FROM email_results
                WHERE execution_id = ?
                  AND technique = ?
            """, (execution_id, metric_name, execution_id, technique))

        # ======================
        # COBERTURA SCRAPING (EMAILS)
        # ======================

        self._execute("""
            INSERT INTO execution_metrics (execution_id, metric, value)
            SELECT ?, 'emails_detected_by_scraping', COUNT(*)
            FROM email_results
            WHERE execution_id = ?
              AND technique IN ('scraping_dom', 'scraping_json')
        """, (execution_id, execution_id))

        self._execute("""
            INSERT INTO execution_metrics (execution_id, metric, value)
            SELECT ?, 'emails_detected_without_scraping', COUNT(*)
            FROM email_results
            WHERE execution_id = ?
              AND technique NOT IN ('scraping_dom', 'scraping_json')
        """, (execution_id, execution_id))

        # ======================
        # LIVE vs WAYBACK
        # ======================

        self._execute("""
            INSERT INTO execution_metrics (execution_id, metric, value)
            SELECT ?, 'emails_from_live', COUNT(*)
            FROM email_results
            WHERE execution_id = ?
              AND context = 'live'
        """, (execution_id, execution_id))

        self._execute("""
            INSERT INTO execution_metrics (execution_id, metric, value)
            SELECT ?, 'emails_from_wayback', COUNT(*)
            FROM email_results
            WHERE execution_id = ?
              AND context = 'wayback'
        """, (execution_id, execution_id))

        # ======================
        # CREDENCIALES
        # ======================

        # Total credenciales
        self._execute("""
            INSERT INTO execution_metrics (execution_id, metric, value)
            SELECT ?, 'creds_total', COUNT(*)
            FROM credential_results
            WHERE execution_id = ?
        """, (execution_id, execution_id))

        # Credenciales por técnica (AQUÍ estaba tu bug)
        rows = self._fetchall("""
            SELECT technique, COUNT(*)
            FROM credential_results
            WHERE execution_id = ?
            GROUP BY technique
        """, (execution_id,))

        for tech, count in rows:
            self._execute("""
                INSERT INTO execution_metrics (execution_id, metric, value)
                VALUES (?, ?, ?)
            """, (execution_id, f"creds_{tech}", count))

        # Cobertura scraping en credenciales
        self._execute("""
            INSERT INTO execution_metrics (execution_id, metric, value)
            SELECT ?, 'creds_detected_by_scraping', COUNT(*)
            FROM credential_results
            WHERE execution_id = ?
              AND technique IN ('scraping_dom', 'scraping_json')
        """, (execution_id, execution_id))

        self._execute("""
            INSERT INTO execution_metrics (execution_id, metric, value)
            SELECT ?, 'creds_detected_without_scraping', COUNT(*)
            FROM credential_results
            WHERE execution_id = ?
              AND technique NOT IN ('scraping_dom', 'scraping_json')
        """, (execution_id, execution_id))


    def get_execution_metrics(self, execution_id: int) -> dict:
        rows = self._fetchall("""
            SELECT metric, value
            FROM execution_metrics
            WHERE execution_id = ?
        """, (execution_id,))

        return {metric: value for metric, value in rows}