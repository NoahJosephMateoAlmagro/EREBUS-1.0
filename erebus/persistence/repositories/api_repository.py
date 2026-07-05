import json

from .base_repository import BaseRepository


class ApiRepository(BaseRepository):
    """
    Repository responsible for retrieving external API credentials.
    """

    def get_provider_credentials(self, provider):
        """
        Retrieves active credentials for a given provider.

        Args:
            provider (str): External API provider name.

        Returns:
            dict | None: Active provider credentials, or None if no enabled credentials exist.
        """
        row = self._fetchone(
            """
            SELECT api_key, extra
            FROM api_credentials
            WHERE provider = ?
            AND enabled = 1
            LIMIT 1
            """,
            (provider,),
        )

        if not row:
            return None

        api_key, extra = row

        return {
            "api_key": api_key,
            "extra": json.loads(extra) if extra else {}
        }