from .base_repository import BaseRepository


class CrawlRepository(BaseRepository):

    def insert_crawler_result(self, execution_id, url, emails, links, scripts):
        """
        Stores the result of a crawled page.
        """

        self._execute("""
            INSERT INTO crawler_results
            (execution_id, url, emails, links, scripts)
            VALUES (?, ?, ?, ?, ?)
        """, (
            execution_id,
            url,
            ",".join(emails or []),
            ",".join(links or []),
            ",".join(scripts or [])
        ))

    def insert_js_result(self, execution_id, script_url, emails, urls):
        """
        Stores the result of JavaScript parsing.
        """

        self._execute("""
            INSERT INTO js_results
            (execution_id, script_url, emails, urls)
            VALUES (?, ?, ?, ?)
        """, (
            execution_id,
            script_url,
            ",".join(emails or []),
            ",".join(urls or [])
        ))