from .base_repository import BaseRepository


class NmapRepository(BaseRepository):
    """
    Repository responsible for persisting Nmap scan results.
    """

    def insert_port(self, execution_id: str, result: dict) -> None:
        """
        Inserts a discovered port from Nmap scan.
        """

        self._execute(
            """
            INSERT INTO nmap_results (
                execution_id,
                ip,
                port,
                protocol,
                state,
                service,
                product,
                version,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execution_id,
                result.get("ip"),
                result.get("port"),
                result.get("protocol"),
                result.get("state"),
                result.get("service"),
                result.get("product"),
                result.get("version"),
                result.get("source"),
            ),
        )