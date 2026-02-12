from .base_repository import BaseRepository


class EmailRepository(BaseRepository):

    def insert_email(self, execution_id, email, domain, technique, source, context):
        self._execute("""
            INSERT INTO email_results
            (execution_id, email, domain, technique, source, context)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (execution_id, email, domain, technique, source, context))