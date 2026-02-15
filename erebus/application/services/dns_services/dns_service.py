class DNSService:
    def __init__(self, context_service, resolution_service, observation_service, headers_service):
        self.context_service = context_service
        self.resolution_service = resolution_service
        self.observation_service = observation_service
        self.headers_service = headers_service

    def run(self, context):
        print("Resolviendo DNS...")

        self.context_service.run(context)
        self.resolution_service.run(context)
        self.observation_service.run(context)

        # headers es “opcional” y NO es DNS puro, pero cuadra aquí en el flujo
        if context.cfg["modules"].get("http_headers"):
            self.headers_service.run(context)
