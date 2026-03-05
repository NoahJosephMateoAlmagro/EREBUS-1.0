from .base_repository import BaseRepository


class NmapRepository(BaseRepository):

    def insert_port(self, execution_id, result):

        self._execute("""
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
        """, (
            execution_id,
            result["ip"],
            result["port"],
            result.get("protocol"),
            result.get("state"),
            result.get("service"),
            result.get("product"),
            result.get("version"),
            result.get("source")
        )) 