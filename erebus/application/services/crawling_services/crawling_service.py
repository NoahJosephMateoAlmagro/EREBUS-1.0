from datetime import datetime

from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class CrawlingService:
    """
    Service responsible for orchestrating seed discovery, live crawling,
    Wayback crawling and post-processing.
    """

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

        target = context.execution.TARGET
        execution_id = context.execution.ID

        Logger.info(
            f"Starting crawling module execution_id={execution_id} target={target}",
            context=self.__class__.__name__
        )

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
            # Seed discovery
            crawl_urls, sources = self.seed_discovery_service.get_seeds(context)
            metrics["seeds_discovered"] = len(crawl_urls)

            # Live crawling
            live_results = self.crawler_live_service.run(
                context,
                crawl_urls,
                sources
            )
            metrics["live_pages"] = len(live_results)

            # Wayback crawling
            wayback_response = self.crawler_wayback_service.run(target)

            if wayback_response.status == ModuleStatus.FAILED:
                response.status = ModuleStatus.FAILED
                response.errors.extend(wayback_response.errors)

                Logger.error(
                    f"Wayback crawling failed execution_id={execution_id} target={target}: "
                    f"{wayback_response.errors}",
                    context=self.__class__.__name__
                )

                return response

            wayback_results = wayback_response.data or []
            metrics["wayback_pages"] = len(wayback_results)

            if wayback_response.metrics:
                metrics.update({
                    f"wayback_{k}": v
                    for k, v in wayback_response.metrics.items()
                })

            # Merge results
            context.live_results = live_results
            context.wayback_results = wayback_results
            context.crawl_results = live_results + wayback_results

            metrics["total_pages"] = len(context.crawl_results)

            # Processing
            processing_metrics = self.crawler_processing_service.run(context) or {}
            metrics.update(processing_metrics)

            response.metrics = metrics

        except CollectorError as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

            Logger.error(
                f"Crawling collector error execution_id={execution_id} target={target}: {e}",
                context=self.__class__.__name__
            )

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"Unexpected error in crawling module: {e}")

            Logger.error(
                f"Unexpected crawling error execution_id={execution_id} target={target}: {e}",
                context=self.__class__.__name__
            )

        finally:
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Finished crawling module execution_id={execution_id} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )

        return response