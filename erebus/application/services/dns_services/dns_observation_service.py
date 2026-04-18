from datetime import datetime

import shared.constants as C
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError
from processing.analyzers.DNS_Details_Analyzer import DNSDetailsAnalyzer
from shared.logger import Logger


class DNSObservationService:
    """
    Service responsible for collecting DNS observations from CNAME and NS records,
    enriching them with provider and exposure analysis, and persisting the results.
    """

    def __init__(self, dns_cname_collector, dns_ns_collector, dns_collector, uow):
        """
        Args:
            dns_cname_collector: Collector responsible for retrieving CNAME records
            dns_ns_collector: Collector responsible for retrieving NS records
            dns_collector: Collector responsible for resolving domains
            uow: Unit of Work for persistence operations
        """
        self.dns_cname_collector = dns_cname_collector
        self.dns_ns_collector = dns_ns_collector
        self.dns_collector = dns_collector
        self.uow = uow

    def run(self, context) -> ModuleResponse:
        """
        Executes DNS observation workflow for discovered domains.

        Args:
            context: Execution context containing discovered domains,
                execution metadata and configuration

        Returns:
            ModuleResponse: Execution result with status, metrics and errors
        """
        target = context.execution.TARGET
        execution_id = context.execution.ID

        Logger.info(
            f"Starting DNS observation module execution_id={execution_id} target={target}",
            context=self.__class__.__name__
        )

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

            base_domain = target
            if base_domain not in domains_to_check:
                domains_to_check.insert(0, base_domain)

            # Analyze every selected domain independently
            for domain in domains_to_check:
                metrics["domains_analyzed"] += 1
                self._analyze_domain(context, domain, metrics)

            response.metrics = metrics

        except CollectorError as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

            Logger.error(
                f"DNS observation collector error execution_id={execution_id} "
                f"target={target}: {e}",
                context=self.__class__.__name__
            )

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"Unexpected error in DNS observation module: {e}")

            Logger.error(
                f"Unexpected DNS observation error execution_id={execution_id} "
                f"target={target}: {e}",
                context=self.__class__.__name__
            )

        finally:
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Finished DNS observation module execution_id={execution_id} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )

        return response

    def _analyze_domain(self, context, domain, metrics) -> None:
        """
        Analyzes CNAME and NS records for a single domain and persists
        the resulting DNS observations.

        Args:
            context: Execution context containing execution metadata
            domain: Domain to inspect
            metrics: Mutable metrics dictionary updated in place
        """

        # ---- CNAME
        cname_results = self.dns_cname_collector.collect(domain)

        for record in cname_results:
            record_value = (record.get("record") or "").strip().lower().rstrip(".")
            if not record_value:
                continue

            metrics["cname_records"] += 1

            provider = DNSDetailsAnalyzer.detect_provider_from_record(record_value, "CNAME")

            target_resolvable = self.uow.domains.get_domain_resolution_status(
                context.execution.ID,
                record_value
            )

            # If the CNAME target has not been evaluated yet, resolve it now
            if target_resolvable is None:
                dns_results = self.dns_collector.collect(record_value)

                if dns_results:
                    self.uow.domains.insert_domain(
                        context.execution.ID,
                        record_value,
                        source=C.TECHNIQUE_DNS_CNAME,
                        status=C.DOMAIN_STATUS_RESOLVABLE
                    )

                    for resolved_record in dns_results:
                        self.uow.domains.insert_resolved_domain(
                            context.execution.ID,
                            resolved_record["domain"],
                            resolved_record["ip"],
                            resolved_record["source"]
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

        for record in ns_results:
            record_value = (record.get("record") or "").strip().lower().rstrip(".")
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