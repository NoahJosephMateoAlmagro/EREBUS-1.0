from exceptions.exceptions import CollectorError
from shared.logger import Logger


class CrawlerLiveService:
    """
    Service responsible for executing live crawling from discovered seed URLs.
    """

    def __init__(self, crawler_cls, timeout, max_pages):
        """
        Args:
            crawler_cls: Crawler class used to execute live crawling
            timeout: HTTP timeout for crawler requests
            max_pages: Maximum number of pages to crawl
        """
        self.crawler_cls = crawler_cls
        self.timeout = timeout
        self.max_pages = max_pages

    def run(self, context, crawl_urls, sources):
        """
        Executes live crawling and annotates discovered pages with their origin.

        Args:
            context: Execution context containing target metadata
            crawl_urls: Seed URLs used to start crawling
            sources: Mapping of URL to origin label

        Returns:
            list[dict]: Crawled page results

        Raises:
            CollectorError: If crawling fails or returns an invalid format
        """
        target = context.execution.TARGET

        Logger.info(
            f"Starting live crawler target={target} seeds={len(crawl_urls)}",
            context=self.__class__.__name__
        )

        try:
            crawler = self.crawler_cls(
                start_url=list(crawl_urls),
                max_pages=self.max_pages,
                timeout=self.timeout,
                allowed_domain=target
            )

            results = crawler.collect()

            if not isinstance(results, list):
                raise CollectorError("Crawler returned invalid result format")

            for page in results:
                if "url" not in page:
                    continue

                page["origin"] = sources.get(page["url"], "live")

            Logger.info(
                f"Finished live crawler target={target} pages={len(results)}",
                context=self.__class__.__name__
            )

            return results

        except CollectorError as e:
            Logger.error(
                f"Live crawler collector error target={target}: {e}",
                context=self.__class__.__name__
            )
            raise

        except Exception as e:
            Logger.error(
                f"Unexpected live crawler error target={target}: {e}",
                context=self.__class__.__name__
            )
            raise CollectorError(f"Live crawler error: {e}") from e