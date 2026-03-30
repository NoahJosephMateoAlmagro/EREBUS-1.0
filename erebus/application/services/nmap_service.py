from datetime import datetime

from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class NmapService:
    """
    Service responsible for orchestrating batched Nmap scans and persisting parsed port results.
    """

    def __init__(self, nmap_collector, nmap_parser, uow, batch_size: int = 5):
        """
        Args:
            nmap_collector: Collector responsible for executing Nmap scans
            nmap_parser: Parser responsible for extracting port results from XML output
            uow: Unit of Work for persistence operations
            batch_size (int): Number of targets scanned per batch
        """
        self.nmap_collector = nmap_collector
        self.nmap_parser = nmap_parser
        self.uow = uow
        self.batch_size = batch_size

    def run(self, context) -> ModuleResponse | None:
        """
        Executes batched Nmap scanning workflow.

        Args:
            context: Execution context containing target and execution metadata

        Returns:
            ModuleResponse: Execution result with status, metrics and errors
        """
        target = context.execution.TARGET
        execution_id = context.execution.ID

        Logger.info(
            f"Starting Nmap module execution_id={execution_id} target={target}",
            context=self.__class__.__name__
        )

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

            if target:
                targets.append(target)

            ips = self.uow.domains.get_resolved_ips(execution_id) or []
            metrics["ips_loaded_from_db"] = len(ips)

            targets.extend(ips)

            deduplicated_targets = list(dict.fromkeys(item for item in targets if item))
            metrics["targets_total"] = len(deduplicated_targets)

            if not deduplicated_targets:
                response.metrics = metrics
                return response

            for i in range(0, len(deduplicated_targets), self.batch_size):
                batch = deduplicated_targets[i:i + self.batch_size]

                Logger.debug(
                    f"Scanning batch index={i // self.batch_size + 1} size={len(batch)} targets={batch}",
                    context=self.__class__.__name__
                )

                try:
                    xml_output = self.nmap_collector.collect(batch)
                    port_results = self.nmap_parser.parse(xml_output)

                    Logger.debug(
                        f"Parsed {len(port_results)} ports for batch index={i // self.batch_size + 1}",
                        context=self.__class__.__name__
                    )

                    for port in port_results:
                        self.uow.nmap.insert_port(execution_id, port)
                        metrics["ports_found"] += 1

                    metrics["targets_scanned"] += len(batch)

                except CollectorError as e:
                    response.errors.append(str(e))

                    Logger.error(
                        f"Nmap batch collector error execution_id={execution_id} "
                        f"target={target} batch={batch}: {e}",
                        context=self.__class__.__name__
                    )

                    continue

                except Exception as e:
                    response.errors.append(f"Unexpected batch error: {e}")

                    Logger.error(
                        f"Unexpected Nmap batch error execution_id={execution_id} "
                        f"target={target} batch={batch}: {e}",
                        context=self.__class__.__name__
                    )

                    continue

            response.metrics = metrics

        except CollectorError as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

            Logger.error(
                f"Nmap collector error execution_id={execution_id} target={target}: {e}",
                context=self.__class__.__name__
            )

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"Unexpected error in Nmap module: {e}")

            Logger.error(
                f"Unexpected Nmap error execution_id={execution_id} target={target}: {e}",
                context=self.__class__.__name__
            )

        finally:
            response.metrics = metrics
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Finished Nmap module execution_id={execution_id} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )

        return response