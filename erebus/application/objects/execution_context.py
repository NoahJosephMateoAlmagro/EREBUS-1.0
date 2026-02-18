from application.execution_stats import ExecutionStats

class ExecutionContext:

    def __init__(self, execution, cfg):
        self.execution = execution
        self.cfg = cfg

        self.stats = ExecutionStats()

        self.seen_emails = set()
        self.seen_creds = set()
        self.seen_domains = set()

        self.all_domains = {execution.TARGET}

        self.live_results = []
        self.wayback_results = []
        self.crawl_results = []

    # -----------------------------
    # Utils - Dedup logic
    # -----------------------------

    def is_new_email(self, email: str) -> bool:
        if email in self.seen_emails:
            return False
        self.seen_emails.add(email)
        return True

    def is_new_credential(self, ctype: str, value: str) -> bool:
        key = (ctype, (value or "").lower())
        if key in self.seen_creds:
            return False
        self.seen_creds.add(key)
        return True

    def _is_new_domain(self, domain, seen):
        if domain in seen:
            return False
        seen.add(domain)
        return True
