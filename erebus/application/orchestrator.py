from application.bootstrap.service_builder import ServiceBuilder
from application.objects.execution_context import ExecutionContext
from shared.domain_validator import is_valid_domain


class Orchestrator:

    def __init__(self, uow):
        self.uow = uow

    def _validate_cfg(self, cfg):
        if cfg is None:
            raise ValueError("Configuración requerida: cfg no puede ser None")

        if not isinstance(cfg, dict):
            raise TypeError("Configuración inválida: cfg debe ser un dict")

        if "modules" not in cfg or "limits" not in cfg or "timeouts" not in cfg:
            raise ValueError(
                "Configuración inválida: se esperaban las claves 'modules', 'limits' y 'timeouts'"
            )

    def run(self, execution, cfg):

        self._validate_cfg(cfg)

        builder = ServiceBuilder(self.uow, cfg, is_valid_domain)
        services = builder.build()

        context = ExecutionContext(execution, cfg)

        if cfg["modules"]["subdomains"]:
            services["subdomain"].run(context)

        if cfg["modules"]["whois"]:
            services["whois"].run(context)

        if cfg["modules"]["dns"]:
            services["dns"].run(context)

        if cfg["modules"]["emails_passive"]:
            services["emails_passive"].run(context)

        if cfg["modules"]["crawler"]:
            services["crawling"].run(context)
            services["crawler_processing"].run(context)

        if cfg["modules"]["js_parsing"]:
            services["js"].run(context)

        if cfg["modules"].get("file_parsing"):
            services["file"].run(context)

        if cfg["modules"]["scraping"]:
            services["scraping"].run(context)

        self.uow.metrics.insert_metrics(execution.ID)

        services["debug"].print_summary(
            execution.ID,
            context.stats
        )
