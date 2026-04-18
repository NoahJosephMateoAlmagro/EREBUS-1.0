import subprocess
import shutil
from pathlib import Path
from collectors.base import Collector
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class NmapCollector(Collector):
    """
    Collector that executes Nmap scans on given targets
    and returns raw XML output.
    """
    def __init__(self, timeout: int = 600, nmap_path: str | None = None):
        """
        Args:
            timeout (int): Execution timeout in seconds
            nmap_path (str | None): Optional custom path to Nmap binary
        """
        self.timeout = timeout
        self.nmap_path = nmap_path

    def _resolve_nmap(self) -> str|None:
        """
        Resolves Nmap binary path from config, PATH or common locations.
        """

        if self.nmap_path and Path(self.nmap_path).exists():
            return self.nmap_path

        path = shutil.which("nmap")
        if path:
            return path

        candidates = [
            r"C:\Program Files\Nmap\nmap.exe",
            r"C:\Program Files (x86)\Nmap\nmap.exe"
        ]

        for p in candidates:
            if Path(p).exists():
                return p

        return None

    def collect(self, targets: str | list[str]) -> str :
        """
        Executes Nmap scan for one or multiple targets.

        Args:
            targets (str | list): Target(s) to scan

        Returns:
            str: Raw XML output from Nmap
        """

        Logger.info(f"Starting Nmap scan for targets: {targets}", context=self.__class__.__name__)

        nmap = self._resolve_nmap()

        if not nmap:
            Logger.error("Nmap not found", context=self.__class__.__name__)
            raise CollectorError("Nmap not installed or not found in config/PATH")

        # Accept string or list
        if isinstance(targets, str):
            targets = [targets]

        if not targets:
            Logger.error("No targets provided", context=self.__class__.__name__)
            raise CollectorError("No targets provided to Nmap")

        try:

            cmd = [
                nmap,
                "-sV",
                "-Pn",
                "--top-ports", "1000",
                "-oX", "-"
            ] + targets

            Logger.debug(f"Executing Nmap scan for {len(targets)} targets", context=self.__class__.__name__)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                Logger.error(f"Nmap execution failed: {result.stderr}", context=self.__class__.__name__)
                raise CollectorError(f"Nmap execution failed: {result.stderr}")

            Logger.info("Nmap scan completed", context=self.__class__.__name__)
            return result.stdout

        except subprocess.TimeoutExpired:
            Logger.error("Nmap execution timeout", context=self.__class__.__name__)
            raise CollectorError(f"Nmap timeout for targets: {targets}")

        except CollectorError: #Inner try errors
            raise

        except Exception as e:
            Logger.error(f"Nmap error: {e}", context=self.__class__.__name__)
            raise CollectorError(f"Nmap error: {e}") from e
