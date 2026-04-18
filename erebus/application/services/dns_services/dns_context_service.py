from datetime import datetime

from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError
from processing.analyzers.DNS_Details_Analyzer import DNSDetailsAnalyzer
from shared.logger import Logger


class DNSContextService:
    """
    Service responsible for collecting MX and TXT records for the base domain,
    analyzing mail-related DNS context and persisting the results.
    """

    def __init__(self, dns_mx_collector, dns_txt_collector, uow):
        """
        Args:
            dns_mx_collector: Collector responsible for retrieving MX records
            dns_txt_collector: Collector responsible for retrieving TXT records
            uow: Unit of Work for persistence operations
        """
        self.dns_mx_collector = dns_mx_collector
        self.dns_txt_collector = dns_txt_collector
        self.uow = uow

    def run(self, context) -> ModuleResponse:
        """
        Executes DNS context workflow for the base domain.

        Args:
            context: Execution context containing execution metadata
                and shared state

        Returns:
            ModuleResponse: Execution result with status, metrics and errors
        """
        target = context.execution.TARGET
        execution_id = context.execution.ID

        Logger.info(
            f"Starting DNS context module execution_id={execution_id} target={target}",
            context=self.__class__.__name__
        )

        response = ModuleResponse(
            module_name="dns_context",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "mx_hosts_found": 0,
            "txt_records_found": 0
        }

        base_domain = target

        try:
            # Collect MX records
            mx_results = self.dns_mx_collector.collect(base_domain)
            mx_hosts = sorted({
                record["record"].lower()
                for record in mx_results
                if record.get("record")
            })

            metrics["mx_hosts_found"] = len(mx_hosts)

            # Collect TXT records
            txt_results = self.dns_txt_collector.collect(base_domain)
            txt_records = [
                record["record"].lower()
                for record in txt_results
                if record.get("record")
            ]

            metrics["txt_records_found"] = len(txt_records)

            # Analyze DNS context related to mail infrastructure
            dns_context = DNSDetailsAnalyzer.analyze_mail_dns_context(
                mx_hosts=mx_hosts,
                txt_records=txt_records
            )

            # Persist aggregated DNS context
            self.uow.domains.update_domain_dns_context(
                execution_id,
                base_domain,
                mx_records=", ".join(mx_hosts) if mx_hosts else None,
                mail_provider=dns_context["mail_provider"],
                spf_policy=dns_context["spf_policy"],
                external_services=", ".join(dns_context["external_services"])
                if dns_context["external_services"] else None
            )

            response.metrics = metrics

        except CollectorError as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

            Logger.error(
                f"DNS context collector error execution_id={execution_id} "
                f"target={target}: {e}",
                context=self.__class__.__name__
            )

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"Unexpected error in DNS context module: {e}")

            Logger.error(
                f"Unexpected DNS context error execution_id={execution_id} "
                f"target={target}: {e}",
                context=self.__class__.__name__
            )

        finally:
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Finished DNS context module execution_id={execution_id} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )

        return response