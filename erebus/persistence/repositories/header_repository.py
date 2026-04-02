from .base_repository import BaseRepository


class HeaderRepository(BaseRepository):
    """
    Repository responsible for storing HTTP header observations.
    """

    def insert_http_header(
        self,
        execution_id: str,
        domain: str,
        url: str,
        header: str,
        value: str | None,
        category: str,
        status: str,
        exposure_level: str,
        description: str,
    ) -> None:
        """
        Inserts an HTTP header observation.
        Uses INSERT OR IGNORE to avoid duplicates based on unique constraints.
        """

        # Minimal validation
        if not header or not url:
            return

        self._execute(
            """
            INSERT OR IGNORE INTO http_headers (
                execution_id,
                domain,
                url,
                header,
                value,
                category,
                status,
                exposure_level,
                description
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execution_id,
                domain,
                url,
                header,
                value,
                category,
                status,
                exposure_level,
                description,
            ),
        )