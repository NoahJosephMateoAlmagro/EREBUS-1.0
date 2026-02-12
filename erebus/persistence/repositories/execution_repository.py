from .base_repository import BaseRepository


class ExecutionRepository(BaseRepository):

    def insert(self, execution):
        self._execute("""
            INSERT INTO executions (id, target, start_time, end_time, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            execution.ID,
            execution.TARGET,
            execution.START.isoformat(),
            execution.END.isoformat() if execution.END else None,
            execution.STATUS
        ))

    def update(self, execution):
        self._execute("""
            UPDATE executions
            SET end_time = ?, status = ?
            WHERE id = ?
        """, (
            execution.END.isoformat() if execution.END else None,
            execution.STATUS,
            execution.ID
        ))