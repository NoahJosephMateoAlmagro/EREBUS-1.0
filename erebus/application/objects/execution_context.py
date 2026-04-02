class ExecutionContext:
    """
    Shared execution context used across all modules.

    Stores execution metadata, configuration and shared state such as
    deduplication sets and intermediate results produced during execution.
    """

    def __init__(self, execution, cfg):
        """
        Initializes the execution context.

        Args:
            execution: Execution object containing metadata (ID, target, timestamps)
            cfg: Global configuration dictionary
        """
        self.execution = execution
        self.cfg = cfg

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
        """
        Checks whether an email is new and registers it if so.

        Args:
            email (str): Email to check

        Returns:
            bool: True if the email is new, False otherwise
        """
        if email in self.seen_emails:
            return False
        self.seen_emails.add(email)
        return True

    def is_new_credential(self, ctype: str, value: str) -> bool:
        """
        Checks whether a credential is new and registers it if so.

        Args:
            ctype (str): Credential type (e.g., user, password, token)
            value (str): Credential value

        Returns:
            bool: True if the credential is new, False otherwise
        """
        key = (ctype, (value or "").lower())
        if key in self.seen_creds:
            return False
        self.seen_creds.add(key)
        return True

    def is_new_domain(self, domain: str) -> bool:
        """
        Checks whether a domain is new and registers it if so.

        Args:
            domain (str): Domain to check

        Returns:
            bool: True if the domain is new, False otherwise
        """
        if domain in self.seen_domains:
            return False
        self.seen_domains.add(domain)
        return True