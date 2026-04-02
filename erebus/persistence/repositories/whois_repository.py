from .base_repository import BaseRepository
from shared.utils import list_to_str


class WhoisRepository(BaseRepository):
    """
    Repository responsible for persisting WHOIS data.
    """

    def insert_whois_result(self, execution_id: str, domain: str, data: dict) -> None:
        """
        Inserts WHOIS information for a given domain.
        """
        self._execute(
            """
            INSERT INTO whois_results (
                execution_id,
                domain,
                registrar,
                creation_date,
                expiration_date,
                updated_date,
                name_servers,
                status,
                emails,
                raw_text
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execution_id,
                domain,
                data.get("registrar"),
                data.get("creation_date"),
                data.get("expiration_date"),
                data.get("updated_date"),
                list_to_str(data.get("name_servers")),
                list_to_str(data.get("status")),
                list_to_str(data.get("emails")),
                data.get("raw_text"),
            ),
        )