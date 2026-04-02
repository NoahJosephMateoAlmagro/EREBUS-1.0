from .base_repository import BaseRepository


class CredentialRepository(BaseRepository):
    """
    Repository responsible for persisting discovered credentials.
    """

    def insert_credential(
        self,
        execution_id: str,
        ctype: str,
        value: str,
        technique: str,
        source: str,
        context: str | None,
    ) -> None:
        """
        Inserts a credential observation.
        Uses INSERT OR IGNORE to avoid duplicates.
        """
        self._execute(
            """
            INSERT OR IGNORE INTO credential_results
            (execution_id, type, value, technique, source, context)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                execution_id,
                ctype,
                value,
                technique,
                source,
                context,
            ),
        )