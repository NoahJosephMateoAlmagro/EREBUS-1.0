from datetime import datetime
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class NmapService:

    def __init__(self, nmap_collector, nmap_parser, uow):
        self.nmap_collector = nmap_collector
        self.nmap_parser = nmap_parser
        self.uow = uow

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

            seen = set()
            dedup_targets = []

            for t in targets:
                if t and t not in seen:
                    seen.add(t)
                    dedup_targets.append(t)

            metrics["targets_total"] = len(dedup_targets)

            print(f"[DEBUG] Total targets to scan: {metrics['targets_total']}")

            max_workers = 5

            print(f"[DEBUG] Starting ThreadPoolExecutor with {max_workers} workers")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:

                future_to_target = {
                    executor.submit(self.nmap_collector.collect, t): t
                    for t in dedup_targets
                }

                for future in as_completed(future_to_target):

                    target = future_to_target[future]
                    thread_name = threading.current_thread().name

                    print(f"[DEBUG] Thread {thread_name} handling result for {target}")

                    metrics["targets_scanned"] += 1

                    try:

                        print(f"[DEBUG] {thread_name} waiting result for {target}")

                        xml_output = future.result()

                        print(f"[DEBUG] {thread_name} scan completed for {target}")

                        port_results = self.nmap_parser.parse(xml_output)

                        print(f"[DEBUG] {thread_name} parsed {len(port_results)} ports for {target}")

                        for port in port_results:

                            self.uow.nmap.insert_port(
                                context.execution.ID,
                                port
                            )

                            metrics["ports_found"] += 1

                    except CollectorError as e:

                        print(f"[DEBUG] ERROR in thread {thread_name} for {target}: {e}")

                        response.errors.append(str(e))

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

            print("[DEBUG] NmapService finished")

            response.finished_at = datetime.utcnow()

        return response