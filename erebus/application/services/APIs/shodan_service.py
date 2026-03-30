from datetime import datetime

import shared.constants as C
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class ShodanService:
    """
    Service responsible for collecting Shodan domain data, discovering subdomains and IPs,
    and enriching discovered hosts with service and port information.
    """

    def __init__(self, shodan_collector, uow, domain_validator):
        """
        Args:
            shodan_collector: Collector responsible for interacting with the Shodan API
            uow: Unit of Work for persistence operations
            domain_validator: Callable used to validate and normalize domains
        """
        self.shodan_collector = shodan_collector
        self.uow = uow
        self._is_valid_domain = domain_validator

    def run(self, context) -> ModuleResponse | None:
        """
        Executes Shodan discovery and host enrichment workflow.

        Args:
            context: Execution context containing target and execution metadata

        Returns:
            ModuleResponse: Execution result with status, metrics and errors
        """
        target = context.execution.TARGET
        execution_id = context.execution.ID

        Logger.info(
            f"Starting Shodan module execution_id={execution_id} target={target}",
            context=self.__class__.__name__
        )

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
            # -------- API key --------
            creds = self.uow.apis.get_provider_credentials("shodan")

            if not creds:
                response.status = ModuleStatus.SKIPPED
                response.errors.append("No Shodan API key configured")

                Logger.info(
                    f"Skipping Shodan module execution_id={execution_id} target={target}: "
                    f"API key not configured",
                    context=self.__class__.__name__
                )

                response.metrics = metrics
                return response

            self.shodan_collector.set_api_key(creds["api_key"])

            # -------- domain discovery --------
            results = self.shodan_collector.collect(target)

            metrics["subdomains_found"] = len(results.get("subdomains", []))

            inserted = 0

            for subdomain in results.get("subdomains", []):
                domain = self._is_valid_domain(subdomain)

                if not domain:
                    continue

                if domain not in context.seen_domains:
                    context.seen_domains.add(domain)
                    context.all_domains.add(domain)

                    self.uow.domains.insert_domain(
                        execution_id,
                        domain,
                        source=C.TECHNIQUE_SHODAN,
                        status=C.DOMAIN_STATUS_NOT_EVALUATED
                    )

                    inserted += 1

            metrics["domains_inserted"] = inserted

            for ip in results.get("ips", []):
                self.uow.domains.insert_resolved_domain(
                    execution_id,
                    target,
                    ip,
                    source=C.TECHNIQUE_SHODAN
                )

                metrics["ips_discovered"] += 1

            # -------- host enrichment by IP --------
            ips = self.uow.domains.get_resolved_ips(execution_id)

            if not ips:
                response.metrics = metrics
                return response

            seen_ports = set()

            for ip in set(ips):
                try:
                    host_data = self.shodan_collector.get_host(ip)

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
                            execution_id,
                            result
                        )

                        metrics["ports_discovered"] += 1

                except Exception as e:
                    Logger.error(
                        f"Shodan host enrichment error execution_id={execution_id} "
                        f"target={target} ip={ip}: {e}",
                        context=self.__class__.__name__
                    )
                    continue

            response.metrics = metrics

        except CollectorError as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

            Logger.error(
                f"Shodan collector error execution_id={execution_id} target={target}: {e}",
                context=self.__class__.__name__
            )

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"Unexpected error in Shodan module: {e}")

            Logger.error(
                f"Unexpected Shodan error execution_id={execution_id} target={target}: {e}",
                context=self.__class__.__name__
            )

        finally:
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Finished Shodan module execution_id={execution_id} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )

        return response