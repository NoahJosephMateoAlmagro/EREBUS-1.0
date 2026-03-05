from datetime import datetime
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError


class NmapService:

    def __init__(self, nmap_collector, nmap_parser, uow):
        self.nmap_collector = nmap_collector
        self.nmap_parser = nmap_parser
        self.uow = uow

    def run(self, context):

        response = ModuleResponse(
            module_name="nmap",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "targets_total": 0,
            "targets_scanned": 0,
            "ports_found": 0,
            "ips_loaded_from_db": 0
        }

        try:

            targets = []

            base = context.execution.TARGET
            if base:
                targets.append(base)

            ips = self.uow.domains.get_resolved_ips(context.execution.ID)
            metrics["ips_loaded_from_db"] = len(ips)

            targets.extend(ips)

            seen = set()
            dedup_targets = []

            for t in targets:
                if t and t not in seen:
                    seen.add(t)
                    dedup_targets.append(t)

            metrics["targets_total"] = len(dedup_targets)

            for t in dedup_targets:

                metrics["targets_scanned"] += 1

                xml_output = self.nmap_collector.collect(t)

                port_results = self.nmap_parser.parse(xml_output)

                for port in port_results:

                    self.uow.nmap.insert_port(
                        context.execution.ID,
                        port
                    )

                    metrics["ports_found"] += 1

            response.metrics = metrics

        except CollectorError as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

        except Exception:
            response.status = ModuleStatus.FAILED
            response.errors.append("Unexpected error in Nmap module")

        finally:
            response.finished_at = datetime.utcnow()

        return response