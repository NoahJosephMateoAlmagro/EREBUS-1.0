from .base_repository import BaseRepository


class ExecutionRepository(BaseRepository):
    """
    Repository responsible for managing execution lifecycle records.
    """

    def insert(self, execution) -> None:
        """
        Inserts a new execution record.
        """
        if not execution.ID or not execution.TARGET:
            return

        self._execute(
            """
            INSERT INTO executions (id, target, start_time, end_time, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                execution.ID,
                execution.TARGET,
                execution.START.isoformat(),
                execution.END.isoformat() if execution.END else None,
                execution.STATUS,
            ),
        )

    def update(self, execution) -> None:
        """
        Updates execution status and end time.
        """
        if not execution.ID:
            return

        self._execute(
            """
            UPDATE executions
            SET end_time = ?, status = ?
            WHERE id = ?
            """,
            (
                execution.END.isoformat() if execution.END else None,
                execution.STATUS,
                execution.ID,
            ),
        )