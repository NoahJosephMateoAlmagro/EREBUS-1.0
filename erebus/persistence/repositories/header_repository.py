from .base_repository import BaseRepository


class HeaderRepository(BaseRepository):

    def insert_http_header(
        self,
        execution_id,
        domain,
        url,
        header,
        value,
        category,
        status,
        exposure_level,
        description
    ):
        self._execute("""
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
        """, (
            execution_id,
            domain,
            url,
            header,
            value,
            category,
            status,
            exposure_level,
            description
        ))