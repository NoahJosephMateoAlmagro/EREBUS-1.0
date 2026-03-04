from datetime import datetime
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError
from processing.analyzers.DNS_Details_Analyzer import DNS_Details_Analyzer


class DNSContextService:

    def __init__(self, dns_mx_collector, dns_txt_collector, uow):
        self.dns_mx_collector = dns_mx_collector
        self.dns_txt_collector = dns_txt_collector
        self.uow = uow

    def run(self, context) -> ModuleResponse | None:

        response = ModuleResponse(
            module_name="dns_context",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "mx_records_found": 0,
            "txt_records_found": 0
        }

        base_domain = context.execution.TARGET

        try:
            mx_results = self.dns_mx_collector.collect(base_domain)
            mx_hosts = sorted({
                r["record"].lower()
                for r in mx_results
                if r.get("record")
            })

            metrics["mx_records_found"] = len(mx_hosts)

            txt_results = self.dns_txt_collector.collect(base_domain)
            txt_records = [
                r["record"].lower()
                for r in txt_results
                if r.get("record")
            ]

            metrics["txt_records_found"] = len(txt_records)

            dns_context = DNS_Details_Analyzer.analyze_mail_dns_context(
                mx_hosts=mx_hosts,
                txt_records=txt_records
            )

            self.uow.domains.update_domain_dns_context(
                context.execution.ID,
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

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append("Unexpected error in DNS context module")

        finally:
            response.finished_at = datetime.utcnow()

        return response