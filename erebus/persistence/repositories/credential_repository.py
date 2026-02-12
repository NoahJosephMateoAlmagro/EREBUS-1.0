from .base_repository import BaseRepository


class CredentialRepository(BaseRepository):

    def insert_credential(self, execution_id, ctype, value, technique, source, context):
        self._execute("""
            INSERT INTO credential_results
            (execution_id, type, value, technique, source, context)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (execution_id, ctype, value, technique, source, context))