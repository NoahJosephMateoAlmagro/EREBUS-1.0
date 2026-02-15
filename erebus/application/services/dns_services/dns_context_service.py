from processing.analyzers.DNS_Details_Analyzer import DNS_Details_Analyzer

class DNSContextService:
    def __init__(self, dns_mx_collector, dns_txt_collector, uow):
        self.dns_mx_collector = dns_mx_collector
        self.dns_txt_collector = dns_txt_collector
        self.uow = uow

    def run(self, context):
        base_domain = context.execution.TARGET
        print(f"[DNS] Analizando MX/TXT del dominio base: {base_domain}")

        mx_results = self.dns_mx_collector.collect(base_domain)
        mx_hosts = sorted({r["record"].lower() for r in mx_results if r.get("record")})

        txt_results = self.dns_txt_collector.collect(base_domain)
        txt_records = [r["value"].lower() for r in txt_results if r.get("value")]

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
            external_services=", ".join(dns_context["external_services"]) if dns_context["external_services"] else None
        )
