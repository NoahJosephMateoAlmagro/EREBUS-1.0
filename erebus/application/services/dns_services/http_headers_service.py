from datetime import datetime

from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError
from processing.analyzers.headers_analyzer import HeadersAnalyzer
from shared.logger import Logger


class HttpHeadersService:
    """
    Service responsible for collecting HTTP headers from discovered domains,
    analyzing them and persisting the results.
    """

    def __init__(self, http_headers_collector, uow):
        """
        Args:
            http_headers_collector: Collector responsible for retrieving HTTP headers
            uow: Unit of Work for persistence operations
        """
        self.http_headers_collector = http_headers_collector
        self.uow = uow

    def run(self, context) -> ModuleResponse:
        """
        Executes HTTP headers collection and analysis workflow.

        Args:
            context: Execution context containing discovered domains,
                execution metadata and configuration

        Returns:
            ModuleResponse: Execution result with status, metrics and errors
        """
        target = context.execution.TARGET
        execution_id = context.execution.ID

        Logger.info(
            f"Starting HTTP headers module execution_id={execution_id} target={target}",
            context=self.__class__.__name__
        )

        response = ModuleResponse(
            module_name="http_headers",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "domains_checked": 0,
            "domains_with_headers": 0,
            "headers_inserted": 0
        }

        try:
            max_dns = int(context.cfg["limits"]["dns_max_domains"])
            domains = list(context.all_domains)[:max_dns]

            # Process each discovered domain independently
            for domain in domains:
                metrics["domains_checked"] += 1

                try:
                    inserted = self._run_for_domain(context, domain)

                    if inserted > 0:
                        metrics["domains_with_headers"] += 1
                        metrics["headers_inserted"] += inserted

                except CollectorError as e:
                    # Non-fatal domain-level error: keep processing remaining domains
                    response.errors.append(f"HTTP headers collection failed for {domain}: {e}")

                    Logger.error(
                        f"HTTP headers collector error execution_id={execution_id} "
                        f"target={target} domain={domain}: {e}",
                        context=self.__class__.__name__
                    )
                    continue

                except Exception as e:
                    # Non-fatal unexpected domain-level error
                    response.errors.append(f"Unexpected HTTP headers error for {domain}: {e}")

                    Logger.error(
                        f"Unexpected HTTP headers domain error execution_id={execution_id} "
                        f"target={target} domain={domain}: {e}",
                        context=self.__class__.__name__
                    )
                    continue

            response.metrics = metrics

        except Exception as e:
            # Fatal module-level error
            response.status = ModuleStatus.FAILED
            response.errors.append(f"Unexpected error in HTTP headers module: {e}")

            Logger.error(
                f"Unexpected HTTP headers module error execution_id={execution_id} "
                f"target={target}: {e}",
                context=self.__class__.__name__
            )

        finally:
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Finished HTTP headers module execution_id={execution_id} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )

        return response

    def _run_for_domain(self, context, domain) -> int:
        """
        Collects and analyzes HTTP headers for a single domain.

        Args:
            context: Execution context containing execution metadata
            domain: Domain to inspect

        Returns:
            int: Number of header analysis rows inserted
        """

        # Try HTTPS first, then WWW variants, then HTTP fallbacks
        urls = [
            f"https://{domain}",
            f"https://www.{domain}",
            f"http://{domain}",
            f"http://www.{domain}",
        ]

        result = None
        used_url = None

        # Try each candidate URL until one returns headers
        for url in urls:
            result = self.http_headers_collector.collect(url)
            if result:
                used_url = url
                break

        # No valid headers found for this domain
        if not result:
            return 0

        # Run header analysis in two categories
        analyses = {
            "security": HeadersAnalyzer.analyze_security(result),
            "tech": HeadersAnalyzer.analyze_tech(result),
        }

        inserted_count = 0

        # Persist every analyzed header row
        for category, headers in analyses.items():
            for header_result in headers:
                self.uow.headers.insert_http_header(
                    context.execution.ID,
                    domain,
                    used_url,
                    header_result["header"],
                    header_result["value"],
                    category,
                    header_result["status"],
                    header_result["exposure_level"],
                    header_result["description"]
                )
                inserted_count += 1

        return inserted_count