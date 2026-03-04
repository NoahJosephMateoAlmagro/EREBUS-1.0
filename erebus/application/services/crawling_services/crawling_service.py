from datetime import datetime
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError


class CrawlingService:

    def __init__(
        self,
        seed_discovery_service,
        crawler_live_service,
        crawler_wayback_service,
        crawler_processing_service,
    ):
        self.seed_discovery_service = seed_discovery_service
        self.crawler_live_service = crawler_live_service
        self.crawler_wayback_service = crawler_wayback_service
        self.crawler_processing_service = crawler_processing_service

    def run(self, context) -> ModuleResponse | None:

        response = ModuleResponse(
            module_name="crawling",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "seeds_discovered": 0,
            "live_pages": 0,
            "wayback_pages": 0,
            "total_pages": 0
        }

        try:
            # 1️⃣ Seed discovery
            crawl_urls, sources = self.seed_discovery_service.get_seeds(context)
            metrics["seeds_discovered"] = len(crawl_urls)

            # 2️⃣ Live crawling
            live_results = self.crawler_live_service.run(
                context,
                crawl_urls,
                sources
            )
            metrics["live_pages"] = len(live_results)

            # 3️⃣ Wayback crawling
            wayback_response = self.crawler_wayback_service.run(
                context.execution.TARGET
            )

            if wayback_response.status == ModuleStatus.FAILED:
                response.status = ModuleStatus.FAILED
                response.errors.extend(wayback_response.errors)
                response.finished_at = datetime.utcnow()
                return response

            wayback_results = wayback_response.data or []
            metrics["wayback_pages"] = len(wayback_results)

            # 🔥 agregamos métricas del submódulo
            if wayback_response.metrics:
                metrics.update({
                    f"wayback_{k}": v
                    for k, v in wayback_response.metrics.items()
                })

            # 4️⃣ Unificación
            context.live_results = live_results
            context.wayback_results = wayback_results
            context.crawl_results = live_results + wayback_results

            metrics["total_pages"] = len(context.crawl_results)

            # 5️⃣ Processing
            processing_metrics = self.crawler_processing_service.run(context)
            metrics.update(processing_metrics)

            response.metrics = metrics

        except CollectorError as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

        except Exception:
            response.status = ModuleStatus.FAILED
            response.errors.append("Unexpected error in crawling module")

        finally:
            response.finished_at = datetime.utcnow()

        return response