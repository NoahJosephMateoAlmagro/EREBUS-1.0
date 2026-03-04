from exceptions.exceptions import CollectorError


class CrawlerLiveService:

    def __init__(self, crawler_cls, timeout, max_pages):
        self.crawler_cls = crawler_cls
        self.timeout = timeout
        self.max_pages = max_pages

    def run(self, context, crawl_urls, sources):

        try:
            crawler = self.crawler_cls(
                start_url=list(crawl_urls),
                max_pages=self.max_pages,
                timeout=self.timeout,
                allowed_domain=context.execution.TARGET
            )

            results = crawler.collect()

            if not isinstance(results, list):
                raise CollectorError("Crawler returned invalid result format")

            for page in results:
                if "url" not in page:
                    continue

                page["origin"] = sources.get(page["url"], "live")

            return results

        except CollectorError:
            raise

        except Exception as e:
            raise CollectorError(f"Live crawler error: {e}")