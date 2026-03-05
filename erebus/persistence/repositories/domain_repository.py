from .base_repository import BaseRepository
import shared.constants as C


class DomainRepository(BaseRepository):

    def insert_domain(self, execution_id, domain, source, status):
        self._execute("""
               INSERT INTO domain_results
               (execution_id, domain, source, status)
               VALUES (?, ?, ?, ?)
           """, (execution_id, domain, source, status))

    def update_domain_status(self, execution_id, domain, status):
        self._execute("""
            UPDATE domain_results
            SET status = ?
            WHERE execution_id = ? AND domain = ?
        """, (status, execution_id, domain))


    def update_domain_dns_context(
        self,
        execution_id,
        domain,
        mx_records=None,
        mail_provider=None,
        spf_policy=None,
        external_services=None
    ):
        self._execute("""
            UPDATE domain_results
            SET
                mx_records = ?,
                mail_provider = ?,
                spf_policy = ?,
                external_services = ?
            WHERE execution_id = ? AND domain = ?
        """, (
            mx_records,
            mail_provider,
            spf_policy,
            external_services,
            execution_id,
            domain
        ))

    def get_dns_mail_summary(self):
        row = self._fetchone("""
            SELECT domain, mx_records, mail_provider, spf_policy, external_services
            FROM domain_results
            WHERE mx_records IS NOT NULL
            LIMIT 1
        """)

        if not row:
            return None

        return {
            "domain": row[0],
            "mx_records": row[1],
            "mail_provider": row[2],
            "spf_policy": row[3],
            "external_services": row[4].split(", ") if row[4] else []
        }
    def get_domain_resolution_status(self, execution_id, domain):

        row = self._fetchone("""
            SELECT 1
            FROM resolved_domain_results
            WHERE execution_id = ? AND domain = ?
            LIMIT 1
        """, (execution_id, domain.lower()))

        if row:
            return True

        row = self._fetchone("""
            SELECT status
            FROM domain_results
            WHERE execution_id = ? AND domain = ?
            LIMIT 1
        """, (execution_id, domain.lower()))

        if row and row[0] == C.DOMAIN_STATUS_NOT_RESOLVABLE:
            return False

        return None
    def insert_resolved_domain(self, execution_id, domain, ip, source):
        self._execute("""
            INSERT INTO resolved_domain_results
            (execution_id, domain, ip, source)
            VALUES (?, ?, ?, ?)
        """, (execution_id, domain, ip, source))

    def get_resolved_ips(self, execution_id: str) -> list[str]:
        rows = self._fetchall("""
            SELECT DISTINCT ip
            FROM resolved_domain_results
            WHERE execution_id = ?
            AND ip IS NOT NULL
            AND ip != ''
        """, (execution_id,))

        return [r[0] for r in rows]

    def insert_dns_observation(
        self,
        execution_id,
        domain,
        record_type,
        record_value,
        source=None,
        technique=None,
        provider=None,
        target_resolvable=None,
        exposure_level=None
    ):
        self._execute("""
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
        """, (
            execution_id,
            (domain.lower() if domain else None),
            (record_type.upper() if record_type else None),
            (record_value.lower() if record_value else None),
            source,
            technique,
            provider,
            (
                1 if target_resolvable is True
                else 0 if target_resolvable is False
                else None
            ),
            exposure_level
        ))