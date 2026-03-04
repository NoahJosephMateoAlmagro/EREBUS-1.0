from datetime import datetime
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError
from processing.analyzers.headers_analyzer import HeadersAnalyzer


class HttpHeadersService:

    def __init__(self, http_headers_collector, uow):
        self.http_headers_collector = http_headers_collector
        self.uow = uow

    def run(self, context) -> ModuleResponse | None:

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

            for domain in domains:
                metrics["domains_checked"] += 1
                inserted = self._run_for_domain(context, domain)

                if inserted > 0:
                    metrics["domains_with_headers"] += 1
                    metrics["headers_inserted"] += inserted

            response.metrics = metrics

        except CollectorError as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

        except Exception:
            response.status = ModuleStatus.FAILED
            response.errors.append("Unexpected error in HTTP headers module")

        finally:
            response.finished_at = datetime.utcnow()

        return response

    def _run_for_domain(self, context, domain) -> int:

        urls = [
            f"https://{domain}",
            f"https://www.{domain}",
            f"http://{domain}",
            f"http://www.{domain}",
        ]

        result = None
        used_url = None

        for url in urls:
            result = self.http_headers_collector.collect(url)
            if result:
                used_url = url
                break

        if not result:
            return 0

        analyses = {
            "security": HeadersAnalyzer.analyze_security(result),
            "tech": HeadersAnalyzer.analyze_tech(result),
        }

        inserted_count = 0

        for category, headers in analyses.items():
            for h in headers:
                self.uow.headers.insert_http_header(
                    context.execution.ID,
                    domain,
                    used_url,
                    h["header"],
                    h["value"],
                    category,
                    h["status"],
                    h["exposure_level"],
                    h["description"]
                )
                inserted_count += 1

        return inserted_count