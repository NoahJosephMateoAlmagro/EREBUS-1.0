class HeadersAnalyzer:
    """
    Analyzer responsible for evaluating HTTP headers for:
    - security posture (missing or present headers)
    - technology exposure (stack fingerprinting)
    """

    SECURITY_HEADERS = {
        "strict-transport-security": "Forces HTTPS",
        "content-security-policy": "Mitigates XSS",
        "x-frame-options": "Clickjacking protection",
        "x-content-type-options": "MIME sniffing protection",
        "referrer-policy": "Controls referrer leakage",
        "permissions-policy": "Controls browser features"
    }

    TECH_HEADERS = {
        # Core stack
        "server": "Web server",
        "x-powered-by": "Backend technology",
        "x-generator": "CMS / Generator",

        # Infra / proxy
        "via": "Proxy / Gateway",
        "x-forwarded-for": "Reverse proxy",
        "x-forwarded-proto": "TLS offloading",

        # Sessions / load balancing
        "set-cookie": "Session technology",

        # Cloud / CDN
        "cf-ray": "Cloudflare identifier",
        "cf-cache-status": "Cloudflare cache",
        "x-amz-cf-id": "AWS CloudFront",
        "x-cache": "Reverse proxy cache",

        # Microsoft stack
        "x-aspnet-version": "ASP.NET version",
        "x-aspnetmvc-version": "ASP.NET MVC version",
    }

    @classmethod
    def analyze_security(cls, headers: dict[str, str]) -> list[dict]:
        """
        Evaluates presence of common security headers.

        Args:
            headers (dict[str, str]): HTTP headers (lowercased)

        Returns:
            list[dict]: Security header analysis
        """
        results = []

        for header, description in cls.SECURITY_HEADERS.items():
            value = headers.get(header)

            if value:
                status = "present"
                exposure = "low"
            else:
                status = "missing"
                exposure = "medium"

            results.append({
                "header": header,
                "value": value,
                "status": status,
                "exposure_level": exposure,
                "description": description
            })

        return results

    @classmethod
    def analyze_tech(cls, headers: dict[str, str]) -> list[dict]:
        """
        Evaluates technology-related headers and estimates exposure level.

        Args:
            headers (dict[str, str]): HTTP headers (lowercased)

        Returns:
            list[dict]: Technology exposure analysis
        """
        results = []

        for header, description in cls.TECH_HEADERS.items():
            value = headers.get(header)
            if not value:
                continue

            value_l = value.lower()
            exposure = "low"

            # -------- version disclosure --------
            if "/" in value:
                exposure = "medium"

            # -------- infrastructure hints --------
            if any(x in value_l for x in [
                "bigip", "f5", "varnish", "haproxy"
            ]):
                exposure = "medium"

            # -------- framework disclosure --------
            if any(x in value_l for x in [
                "php/", "asp.net", "django", "flask",
                "spring", "laravel", "rails", "node"
            ]):
                exposure = "high"

            # -------- known CDNs (lower risk) --------
            if any(x in value_l for x in [
                "cloudflare", "github.com"
            ]):
                exposure = "low"

            results.append({
                "header": header,
                "value": value,
                "status": "present",
                "exposure_level": exposure,
                "description": description
            })

        return results