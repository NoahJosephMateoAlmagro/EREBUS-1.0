from datetime import datetime
import shared.constants as C
from application.objects.responses.ModuleResponse import ModuleResponse
from application.objects.responses.ModuleResponse import ModuleStatus
from exceptions.exceptions import CollectorError


class ShodanService:

    def __init__(self, shodan_collector, uow, domain_validator):
        self.shodan_collector = shodan_collector
        self.uow = uow
        self._is_valid_domain = domain_validator

    def run(self, context) -> ModuleResponse | None:

        response = ModuleResponse(
            module_name="shodan",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "subdomains_found": 0,
            "domains_inserted": 0,
            "ips_discovered": 0,
            "hosts_found": 0,
            "ports_discovered": 0
        }

        try:

            print("\n========== SHODAN MODULE START ==========")

            # -------------------------------
            # API KEY
            # -------------------------------

            creds = self.uow.apis.get_provider_credentials("shodan")

            if not creds:
                print("Shodan API key not configured")
                response.status = ModuleStatus.SKIPPED
                response.errors.append("No Shodan API key configured")
                return response

            self.shodan_collector.set_api_key(creds["api_key"])

            print("Shodan API key loaded")

            # ===============================
            # FASE 1 — descubrimiento dominio
            # ===============================

            results = self.shodan_collector.collect(context.execution.TARGET)

            print("RAW SHODAN COLLECT RESULTS:")
            print(results)

            # -------------------------------
            # SUBDOMAINS
            # -------------------------------

            metrics["subdomains_found"] = len(results.get("subdomains", []))

            print("Subdomains discovered:", metrics["subdomains_found"])

            inserted = 0

            for subdomain in results.get("subdomains", []):

                domain = self._is_valid_domain(subdomain)

                if not domain:
                    continue

                if domain not in context.seen_domains:

                    print("New domain discovered from Shodan:", domain)

                    context.seen_domains.add(domain)
                    context.all_domains.add(domain)

                    self.uow.domains.insert_domain(
                        context.execution.ID,
                        domain,
                        source=C.TECHNIQUE_SHODAN,
                        status=C.DOMAIN_STATUS_NOT_EVALUATED
                    )

                    inserted += 1

            metrics["domains_inserted"] = inserted

            print("Domains inserted:", inserted)

            # -------------------------------
            # IPS DISCOVERED
            # -------------------------------

            for ip in results.get("ips", []):

                print("IP discovered by Shodan:", ip)

                self.uow.domains.insert_resolved_domain(
                    context.execution.ID,
                    context.execution.TARGET,
                    ip,
                    source=C.TECHNIQUE_SHODAN
                )

                metrics["ips_discovered"] += 1

            # ===============================
            # FASE 2 — enriquecimiento por IP
            # ===============================

            ips = self.uow.domains.get_resolved_ips(context.execution.ID)

            print("IPS AVAILABLE FOR SHODAN ENRICHMENT:")
            print(ips)

            if not ips:
                response.metrics = metrics
                return response

            seen_ports = set()

            for ip in set(ips):

                try:

                    print("\nQuerying Shodan host info for:", ip)

                    host_data = self.shodan_collector.get_host(ip)

                    print("SHODAN HOST RESPONSE:", host_data)

                    if not host_data:
                        continue

                    metrics["hosts_found"] += 1

                    for service in host_data.get("services", []):

                        port = service.get("port")

                        if not port:
                            continue

                        key = (ip, port, service.get("transport"))

                        if key in seen_ports:
                            continue

                        seen_ports.add(key)

                        print("Discovered service:",
                              ip,
                              port,
                              service.get("product"),
                              service.get("version"))

                        result = {
                            "ip": ip,
                            "port": port,
                            "protocol": service.get("transport"),
                            "state": "open",
                            "service": service.get("product"),
                            "product": service.get("product"),
                            "version": service.get("version"),
                            "source": "shodan"
                        }

                        self.uow.nmap.insert_port(
                            context.execution.ID,
                            result
                        )

                        metrics["ports_discovered"] += 1

                except Exception as e:

                    print("Shodan error for IP:", ip)
                    print(e)
                    continue

            print("\nSHODAN METRICS:", metrics)

            response.metrics = metrics

        except CollectorError as e:

            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

        except Exception as e:

            response.status = ModuleStatus.FAILED
            response.errors.append("Unexpected error in shodan module")
            print(e)

        finally:

            response.finished_at = datetime.utcnow()

            print("========== SHODAN MODULE END ==========\n")

        return response