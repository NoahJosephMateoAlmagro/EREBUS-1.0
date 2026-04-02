from .base_repository import BaseRepository
import shared.constants as C


class DomainRepository(BaseRepository):
    """
    Repository responsible for managing domain discovery, DNS resolution,
    and DNS observation persistence.
    """

    def insert_domain(
        self,
        execution_id: str,
        domain: str,
        source: str,
        status: str,
    ) -> None:
        """
        Inserts a discovered domain.
        Uses INSERT OR IGNORE to avoid duplicates.
        """
        if not execution_id or not domain:
            return

        self._execute(
            """
            INSERT OR IGNORE INTO domain_results
            (execution_id, domain, source, status)
            VALUES (?, ?, ?, ?)
            """,
            (execution_id, domain.lower(), source, status),
        )

    def update_domain_status(
        self,
        execution_id: str,
        domain: str,
        status: str,
    ) -> None:
        """
        Updates the resolution status of a domain.
        """
        if not execution_id or not domain:
            return

        self._execute(
            """
            UPDATE domain_results
            SET status = ?
            WHERE execution_id = ? AND domain = ?
            """,
            (status, execution_id, domain.lower()),
        )

    def update_domain_dns_context(
        self,
        execution_id: str,
        domain: str,
        mx_records: str | None = None,
        mail_provider: str | None = None,
        spf_policy: str | None = None,
        external_services: str | None = None,
    ) -> None:
        """
        Updates DNS-related context for a domain.
        """
        if not execution_id or not domain:
            return

        self._execute(
            """
            UPDATE domain_results
            SET
                mx_records = ?,
                mail_provider = ?,
                spf_policy = ?,
                external_services = ?
            WHERE execution_id = ? AND domain = ?
            """,
            (
                mx_records,
                mail_provider,
                spf_policy,
                external_services,
                execution_id,
                domain.lower(),
            ),
        )

    def get_dns_mail_summary(self):
        """
        Retrieves a sample domain with DNS mail context.
        """
        row = self._fetchone(
            """
            SELECT domain, mx_records, mail_provider, spf_policy, external_services
            FROM domain_results
            WHERE mx_records IS NOT NULL
            LIMIT 1
            """
        )

        if not row:
            return None

        return {
            "domain": row[0],
            "mx_records": row[1],
            "mail_provider": row[2],
            "spf_policy": row[3],
            "external_services": row[4].split(", ") if row[4] else [],
        }

    def get_domain_resolution_status(
        self,
        execution_id: str,
        domain: str,
    ) -> bool | None:
        """
        Determines domain resolution status.
        """
        if not execution_id or not domain:
            return None

        domain = domain.lower()

        row = self._fetchone(
            """
            SELECT 1
            FROM resolved_domain_results
            WHERE execution_id = ? AND domain = ?
            LIMIT 1
            """,
            (execution_id, domain),
        )

        if row:
            return True

        row = self._fetchone(
            """
            SELECT status
            FROM domain_results
            WHERE execution_id = ? AND domain = ?
            LIMIT 1
            """,
            (execution_id, domain),
        )

        if row and row[0] == C.DOMAIN_STATUS_NOT_RESOLVABLE:
            return False

        return None

    def insert_resolved_domain(
        self,
        execution_id: str,
        domain: str,
        ip: str,
        source: str,
    ) -> None:
        """
        Inserts a resolved domain (domain -> IP).
        Uses INSERT OR IGNORE to avoid duplicates.
        """
        if not execution_id or not domain or not ip:
            return

        self._execute(
            """
            INSERT OR IGNORE INTO resolved_domain_results
            (execution_id, domain, ip, source)
            VALUES (?, ?, ?, ?)
            """,
            (execution_id, domain.lower(), ip, source),
        )

    def get_resolved_ips(self, execution_id: str) -> list[str]:
        """
        Retrieves all distinct resolved IPs for an execution.
        """
        rows = self._fetchall(
            """
            SELECT DISTINCT ip
            FROM resolved_domain_results
            WHERE execution_id = ?
            AND ip IS NOT NULL
            AND ip != ''
            """,
            (execution_id,),
        )

        return [r[0] for r in rows]

    def insert_dns_observation(
        self,
        execution_id: str,
        domain: str,
        record_type: str,
        record_value: str,
        source: str | None = None,
        technique: str | None = None,
        provider: str | None = None,
        target_resolvable: bool | None = None,
        exposure_level: str | None = None,
    ) -> None:
        """
        Inserts a DNS observation (CNAME / NS).
        Uses INSERT OR IGNORE to avoid duplicates.
        """
        if not execution_id or not domain or not record_type or not record_value:
            return

        self._execute(
            """
            INSERT OR IGNORE INTO dns_observations (
                execution_id,
                domain,
                record_type,
                record_value,
                source,
                technique,
                provider,
                target_resolvable,
                exposure_level
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execution_id,
                domain.lower(),
                record_type.upper(),
                record_value.lower(),
                source,
                technique,
                provider,
                1 if target_resolvable is True else 0 if target_resolvable is False else None,
                exposure_level,
            ),
        )