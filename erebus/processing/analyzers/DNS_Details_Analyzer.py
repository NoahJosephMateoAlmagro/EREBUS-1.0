
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

class DNS_Details_Analyzer:

    @staticmethod
    def analyze_mail_dns_context(mx_hosts: list[str], txt_records: list[str]) -> dict:
        """
        Analiza contexto DNS de correo de un dominio base.
        """

        mail_provider = None
        spf_policy = None
        external_services = []

        # -----------------
        # MX provider
        # -----------------
        if any("google.com" in mx for mx in mx_hosts):
            mail_provider = "Google"
        elif any("outlook.com" in mx or "protection.outlook.com" in mx for mx in mx_hosts):
            mail_provider = "Microsoft"
        elif mx_hosts:
            mail_provider = "Custom / On-prem"

        # -----------------
        # SPF
        # -----------------
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
        record: hostname del CNAME/NS ya normalizado (lower, sin punto final)
        record_type: 'CNAME' o 'NS'
        """
        if not record:
            return "Unknown"

        patterns = CNAME_PROVIDER_PATTERNS if record_type == "CNAME" else NS_PROVIDER_PATTERNS

        for pattern, provider in patterns.items():
            if pattern in record:
                return provider

        return "Unknown"

    @staticmethod
    def is_interesting_dns_observation(record_type: str, provider: str, target_resolvable: bool | None) -> bool:
        """
        Regla simple:
        - CNAME a proveedor conocido y NO resolvable => interesante (posible dangling)
        - Puedes ampliar reglas luego.
        """
        if record_type == "CNAME":
            if provider != "Unknown" and target_resolvable is False:
                return True
        return False

    """
            Cálculo del nivel de exposición OSINT (exposure_level) a partir de observaciones DNS pasivas.

            El exposure_level NO indica una vulnerabilidad confirmada, sino un grado de exposición
            potencial inferido a partir de patrones conocidos de configuración DNS, sin realizar
            explotación activa.

            Escala utilizada:
                - NONE   : Observación normal, sin señales relevantes.
                - LOW    : Dependencia externa conocida, sin anomalías.
                - MEDIUM : Información incompleta o ambigua.
                - HIGH   : Patrón clásico asociado a configuraciones potencialmente inseguras.

            Casos evaluados:

            1) Registros CNAME
               - provider == "Unknown"
                    → NONE
                    (No se puede inferir dependencia externa relevante)

               - provider conocido AND target_resolvable == True
                    → LOW
                    (Dependencia externa válida y operativa)

               - provider conocido AND target_resolvable == False
                    → HIGH
                    (CNAME a proveedor conocido que no resuelve actualmente;
                     patrón asociado a exposición potencial, p. ej. CNAME colgante)

               - provider conocido AND target_resolvable == None
                    → MEDIUM
                    (No se ha podido determinar resolubilidad del target)

            2) Registros NS
               - provider == "Unknown"
                    → NONE
                    (Servidor de nombres sin fingerprint identificable)

               - provider conocido
                    → LOW
                    (Uso de proveedor DNS externo conocido; información contextual)

            Este enfoque permite clasificar observaciones DNS de forma gradual y defendible,
            manteniendo el análisis estrictamente en el ámbito OSINT pasivo.
            """

    @staticmethod
    def calculate_exposure_level(record_type: str,provider: str, target_resolvable: bool | None) -> str:
        """
        Devuelve el nivel de exposición OSINT:
        NONE | LOW | MEDIUM | HIGH
        """

        rt = (record_type or "").strip().upper()
        provider = provider or "Unknown"

        # -----------------
        # CNAME
        # -----------------
        if rt == "CNAME":

            if provider == "Unknown":
                return "NONE"

            if target_resolvable is True:
                return "LOW"

            if target_resolvable is False:
                return "HIGH"

            # Caso raro: no se pudo resolver
            return "MEDIUM"

        # -----------------
        # NS
        # -----------------
        if rt == "NS":
            if provider == "Unknown":
                return "NONE"
            return "LOW"

        # -----------------
        # Otros (futuro)
        # -----------------
        return "NONE"