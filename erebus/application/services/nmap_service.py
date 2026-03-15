from datetime import datetime

from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError


class NmapService:

    def __init__(self, nmap_collector, nmap_parser, uow, batch_size: int = 5):
        self.nmap_collector = nmap_collector
        self.nmap_parser = nmap_parser
        self.uow = uow
        self.batch_size = batch_size

    def run(self, context):

        print("\n[DEBUG] NmapService started")

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
                print(f"[DEBUG] Base target: {base}")
                targets.append(base)

            ips = self.uow.domains.get_resolved_ips(context.execution.ID)
            metrics["ips_loaded_from_db"] = len(ips)

            print(f"[DEBUG] Loaded {len(ips)} IPs from DB")

            targets.extend(ips)

            # deduplicado
            dedup_targets = list(dict.fromkeys(t for t in targets if t))
            metrics["targets_total"] = len(dedup_targets)

            print(f"[DEBUG] Total targets to scan: {metrics['targets_total']}")

            if not dedup_targets:
                print("[DEBUG] No targets to scan")
                return response

            # -------- escaneo por lotes (para mejorar un poco la ejecucion utilizando la concurrencia de nmap pero sin sobrecargarlo --------

            for i in range(0, len(dedup_targets), self.batch_size):

                batch = dedup_targets[i:i + self.batch_size]

                print(f"[DEBUG] Scanning batch {i // self.batch_size + 1}: {batch}")

                try:

                    xml_output = self.nmap_collector.collect(batch)

                    port_results = self.nmap_parser.parse(xml_output)

                    print(f"[DEBUG] Parsed {len(port_results)} ports in batch")

                    for port in port_results:
                        self.uow.nmap.insert_port(
                            context.execution.ID,
                            port
                        )
                        metrics["ports_found"] += 1

                    metrics["targets_scanned"] += len(batch)

                except CollectorError as e:

                    print(f"[DEBUG] Batch failed: {batch} -> {e}")

                    response.errors.append(str(e))

                    # no paramos el sistema, seguimos con el siguiente batch
                    continue

        except CollectorError as e:

            print(f"[DEBUG] CollectorError in NmapService: {e}")

            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

        except Exception as e:

            print(f"[DEBUG] Unexpected error in NmapService: {e}")

            response.status = ModuleStatus.FAILED
            response.errors.append("Unexpected error in Nmap module")

        finally:

            response.metrics = metrics
            response.finished_at = datetime.utcnow()

            print("[DEBUG] NmapService finished")

        return response