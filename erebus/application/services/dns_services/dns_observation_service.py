from datetime import datetime
import shared.constants as C
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError
from processing.analyzers.DNS_Details_Analyzer import DNSDetailsAnalyzer


class DNSObservationService:

    def __init__(self, dns_cname_collector, dns_ns_collector, dns_collector, uow):
        self.dns_cname_collector = dns_cname_collector
        self.dns_ns_collector = dns_ns_collector
        self.dns_collector = dns_collector
        self.uow = uow

    def run(self, context) -> ModuleResponse | None:

        response = ModuleResponse(
            module_name="dns_observation",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "domains_analyzed": 0,
            "cname_records": 0,
            "ns_records": 0,
            "observations_inserted": 0
        }

        try:
            max_dns = int(context.cfg["limits"]["dns_max_domains"])
            domains_to_check = list(context.all_domains)[:max_dns]

            base_domain = context.execution.TARGET
            if base_domain not in domains_to_check:
                domains_to_check.insert(0, base_domain)

            for domain in domains_to_check:
                metrics["domains_analyzed"] += 1
                self._analyze_domain(context, domain, metrics)

            response.metrics = metrics

        except CollectorError as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

        except Exception:
            response.status = ModuleStatus.FAILED
            response.errors.append("Unexpected error in DNS observation module")

        finally:
            response.finished_at = datetime.utcnow()

        return response

    def _analyze_domain(self, context, domain, metrics):

        # ---- CNAME
        cname_results = self.dns_cname_collector.collect(domain)

        for r in cname_results:
            record_value = (r.get("record") or "").strip().lower().rstrip(".")
            if not record_value:
                continue

            metrics["cname_records"] += 1

            provider = DNSDetailsAnalyzer.detect_provider_from_record(record_value, "CNAME")

            target_resolvable = self.uow.domains.get_domain_resolution_status(
                context.execution.ID,
                record_value
            )

            if target_resolvable is None:
                dns_results = self.dns_collector.collect(record_value)

                if dns_results:
                    self.uow.domains.insert_domain(
                        context.execution.ID,
                        record_value,
                        source=C.TECHNIQUE_DNS_CNAME,
                        status=C.DOMAIN_STATUS_RESOLVABLE
                    )

                    for rr in dns_results:
                        self.uow.domains.insert_resolved_domain(
                            context.execution.ID,
                            rr["domain"],
                            rr["ip"],
                            rr["source"]
                        )

                    target_resolvable = True
                else:
                    self.uow.domains.insert_domain(
                        context.execution.ID,
                        record_value,
                        source=C.TECHNIQUE_DNS_CNAME,
                        status=C.DOMAIN_STATUS_NOT_RESOLVABLE
                    )
                    target_resolvable = False

            exposure_level = DNSDetailsAnalyzer.calculate_exposure_level(
                record_type="CNAME",
                provider=provider,
                target_resolvable=target_resolvable
            )

            self.uow.domains.insert_dns_observation(
                context.execution.ID,
                domain,
                "CNAME",
                record_value,
                source="dns_resolver",
                technique=C.TECHNIQUE_DNS_CNAME,
                provider=provider,
                target_resolvable=target_resolvable,
                exposure_level=exposure_level
            )

            metrics["observations_inserted"] += 1

        # ---- NS
        ns_results = self.dns_ns_collector.collect(domain)

        for r in ns_results:
            record_value = (r.get("record") or "").strip().lower().rstrip(".")
            if not record_value:
                continue

            metrics["ns_records"] += 1

            provider = DNSDetailsAnalyzer.detect_provider_from_record(record_value, "NS")

            exposure_level = DNSDetailsAnalyzer.calculate_exposure_level(
                record_type="NS",
                provider=provider,
                target_resolvable=None
            )

            self.uow.domains.insert_dns_observation(
                context.execution.ID,
                domain,
                "NS",
                record_value,
                source="dns_resolver",
                technique=C.TECHNIQUE_DNS_NS,
                provider=provider,
                target_resolvable=None,
                exposure_level=exposure_level
            )

            metrics["observations_inserted"] += 1