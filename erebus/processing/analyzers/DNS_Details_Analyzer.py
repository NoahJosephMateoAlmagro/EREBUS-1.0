from typing import Any


CNAME_PROVIDER_PATTERNS = {
    "cloudfront.net": "AWS",
    "amazonaws.com": "AWS",
    "azurewebsites.net": "Azure",
    "trafficmanager.net": "Azure",
    "cloudapp.azure.com": "Azure",
    "herokudns.com": "Heroku",
    "github.io": "GitHub Pages",
    "pages.dev": "Cloudflare Pages",
    "cdn.cloudflare.net": "Cloudflare",
    "fastly.net": "Fastly",
    "netlify.app": "Netlify",
    "vercel.app": "Vercel",
}

NS_PROVIDER_PATTERNS = {
    "cloudflare.com": "Cloudflare",
    "googledomains.com": "Google",
    "domaincontrol.com": "GoDaddy",
    "awsdns-": "AWS Route 53",
    "azure-dns.": "Azure DNS",
    "registrar-servers.com": "Namecheap",
    "ovh.net": "OVH",
}


class DNSDetailsAnalyzer:
    """
    Analyzer responsible for extracting contextual insights from DNS records,
    including provider detection and exposure estimation.
    """

    @staticmethod
    def analyze_mail_dns_context(mx_hosts: list[str], txt_records: list[str]) -> dict[str, Any]:
        """
        Analyzes email-related DNS configuration (MX and SPF).

        Returns:
            dict containing mail provider, SPF policy and external services
        """
        mail_provider = None
        spf_policy = None
        external_services = []

        # -------- MX provider --------
        if any("google.com" in mx for mx in mx_hosts):
            mail_provider = "Google"
        elif any("outlook.com" in mx or "protection.outlook.com" in mx for mx in mx_hosts):
            mail_provider = "Microsoft"
        elif mx_hosts:
            mail_provider = "Custom / On-prem"

        # -------- SPF policy --------
        for txt in txt_records:
            if txt.startswith("v=spf1"):

                if "-all" in txt:
                    spf_policy = "strict"
                elif "~all" in txt:
                    spf_policy = "permissive"
                elif "+all" in txt:
                    spf_policy = "open"
                else:
                    spf_policy = "neutral"

                if "include:_spf.google.com" in txt:
                    external_services.append("Google")

                if "include:spf.protection.outlook.com" in txt:
                    external_services.append("Microsoft")

                break

        return {
            "mail_provider": mail_provider,
            "spf_policy": spf_policy,
            "external_services": sorted(set(external_services))
        }

    @staticmethod
    def detect_provider_from_record(record: str, record_type: str) -> str:
        """
        Detects infrastructure provider based on DNS record patterns.
        """
        if not record:
            return "Unknown"

        rt = (record_type or "").upper()

        patterns = (
            CNAME_PROVIDER_PATTERNS
            if rt == "CNAME"
            else NS_PROVIDER_PATTERNS
        )

        for pattern, provider in patterns.items():
            if pattern in record:
                return provider

        return "Unknown"

    @staticmethod
    def is_interesting_dns_observation(record_type: str, provider: str, target_resolvable: bool | None) -> bool:
        """
        Identifies potentially interesting DNS observations.

        Example:
            - CNAME pointing to known provider and not resolvable
        """
        rt = (record_type or "").upper()

        if rt == "CNAME":
            if provider != "Unknown" and target_resolvable is False:
                return True

        return False

    @staticmethod
    def calculate_exposure_level(record_type: str, provider: str, target_resolvable: bool | None) -> str:
        """
        Calculates OSINT exposure level based on DNS observations.

        Exposure levels:
            NONE | LOW | MEDIUM | HIGH
        """
        rt = (record_type or "").strip().upper()
        provider = provider or "Unknown"

        # -------- CNAME --------
        if rt == "CNAME":

            if provider == "Unknown":
                return "NONE"

            if target_resolvable is True:
                return "LOW"

            if target_resolvable is False:
                return "HIGH"

            return "MEDIUM"

        # -------- NS --------
        if rt == "NS":
            if provider == "Unknown":
                return "NONE"
            return "LOW"

        return "NONE"