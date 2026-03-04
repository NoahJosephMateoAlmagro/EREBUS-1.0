from .base_repository import BaseRepository


class MetricsRepository(BaseRepository):

    def insert_module_metrics(self, execution_id: str, module_name: str, metrics: dict):

        for metric_name, value in metrics.items():

            self._execute("""
                INSERT OR REPLACE INTO execution_metrics
                (execution_id, module_name, metric_name, metric_value)
                VALUES (?, ?, ?, ?)
            """, (
                execution_id,
                module_name,
                metric_name,
                value
            ))

    # ------------------------------------------------
    # Métricas analíticas derivadas
    # ------------------------------------------------

    def insert_derived_metrics(self, execution_id: str):

        # borrar métricas analíticas anteriores
        self._execute("""
            DELETE FROM execution_metrics
            WHERE execution_id = ?
            AND module_name = 'analytics'
        """, (execution_id,))

        # ---------------------
        # EMAILS
        # ---------------------

        self._execute("""
            INSERT INTO execution_metrics
            (execution_id, module_name, metric_name, metric_value)

            SELECT ?, 'analytics', 'emails_total', COUNT(*)
            FROM email_results
            WHERE execution_id = ?
        """, (execution_id, execution_id))

        self._execute("""
            INSERT INTO execution_metrics
            (execution_id, module_name, metric_name, metric_value)

            SELECT ?, 'analytics', 'emails_detected_by_scraping', COUNT(*)
            FROM email_results
            WHERE execution_id = ?
              AND technique IN ('scraping_dom', 'scraping_json')
        """, (execution_id, execution_id))

        self._execute("""
            INSERT INTO execution_metrics
            (execution_id, module_name, metric_name, metric_value)

            SELECT ?, 'analytics', 'emails_detected_without_scraping', COUNT(*)
            FROM email_results
            WHERE execution_id = ?
              AND technique NOT IN ('scraping_dom', 'scraping_json')
        """, (execution_id, execution_id))

        # ---------------------
        # CREDENTIALS
        # ---------------------

        self._execute("""
            INSERT INTO execution_metrics
            (execution_id, module_name, metric_name, metric_value)

            SELECT ?, 'analytics', 'creds_total', COUNT(*)
            FROM credential_results
            WHERE execution_id = ?
        """, (execution_id, execution_id))

    # ------------------------------------------------
    # Obtener métricas
    # ------------------------------------------------

    def get_execution_metrics(self, execution_id: str):

        rows = self._fetchall("""
            SELECT module_name, metric_name, metric_value
            FROM execution_metrics
            WHERE execution_id = ?
        """, (execution_id,))

        result = {}

        for module, metric, value in rows:
            result.setdefault(module, {})[metric] = value

        return result