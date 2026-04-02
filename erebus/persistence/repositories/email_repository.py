from .base_repository import BaseRepository


class EmailRepository(BaseRepository):
    """
    Repository responsible for persisting discovered email addresses.
    """

    def insert_email(
        self,
        execution_id: str,
        email: str,
        domain: str | None,
        technique: str,
        source: str,
        context: str,
    ) -> None:
        """
        Inserts an email observation.

        Uses INSERT OR IGNORE to avoid duplicates based on unique constraint (just to be sure, no duplicates should
        reach this point)

        """

        # Minimal validation
        if not email:
            return

        self._execute(
            """
            INSERT OR IGNORE INTO email_results
            (execution_id, email, domain, technique, source, context)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                execution_id,
                email,
                domain,
                technique,
                source,
                context,
            ),
        )