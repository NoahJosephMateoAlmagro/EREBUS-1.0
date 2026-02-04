class HeadersAnalyzer:

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

        # Sessions / LB
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
    def analyze_security(cls, headers: dict) -> list:
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
    def analyze_tech(cls, headers: dict) -> list:
        results = []

        for header, description in cls.TECH_HEADERS.items():
            value = headers.get(header)
            if not value:
                continue

            value_l = value.lower()
            exposure = "low"

            # ---------------------------
            # Version disclosure
            # ---------------------------
            if "/" in value:
                exposure = "medium"

            # ---------------------------
            # Infra interna / LB
            # ---------------------------
            if any(x in value_l for x in [
                "bigip", "f5", "varnish", "haproxy"
            ]):
                exposure = "medium"

            # ---------------------------
            # Frameworks explícitos
            # ---------------------------
            if any(x in value_l for x in [
                "php/", "asp.net", "django", "flask",
                "spring", "laravel", "rails", "node"
            ]):
                exposure = "high"

            # ---------------------------
            # CDN conocidos (bajan riesgo)
            # ---------------------------
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

