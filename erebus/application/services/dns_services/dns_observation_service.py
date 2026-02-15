import shared.constants as C
from processing.analyzers.DNS_Details_Analyzer import DNS_Details_Analyzer

class DNSObservationService:
    def __init__(self, dns_cname_collector, dns_ns_collector, dns_collector, uow):
        self.dns_cname_collector = dns_cname_collector
        self.dns_ns_collector = dns_ns_collector
        self.dns_collector = dns_collector
        self.uow = uow

    def run(self, context):
        max_dns = int(context.cfg["limits"]["dns_max_domains"])
        domains_to_check = list(context.all_domains)[:max_dns]

        for domain in domains_to_check:
            self._analyze_domain(context, domain)

    def _analyze_domain(self, context, domain):
        print(f"[DNS-OBS] Analizando {domain}")

        # ---- CNAME
        cname_results = self.dns_cname_collector.collect(domain)
        for r in cname_results:
            record_value = (r.get("record") or "").strip().lower().rstrip(".")
            if not record_value:
                continue

            provider = DNS_Details_Analyzer.detect_provider_from_record(record_value, "CNAME")

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

            exposure_level = DNS_Details_Analyzer.calculate_exposure_level(
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

        # ---- NS
        ns_results = self.dns_ns_collector.collect(domain)
        for r in ns_results:
            record_value = (r.get("record") or "").strip().lower().rstrip(".")
            if not record_value:
                continue

            provider = DNS_Details_Analyzer.detect_provider_from_record(record_value, "NS")
            exposure_level = DNS_Details_Analyzer.calculate_exposure_level(
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
