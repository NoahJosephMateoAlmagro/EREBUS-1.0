import subprocess
import shutil
from pathlib import Path
from collectors.base import Collector
from exceptions.exceptions import CollectorError


class NmapCollector(Collector):

    def __init__(self, timeout: int = 600, nmap_path: str | None = None):
        self.timeout = timeout
        self.nmap_path = nmap_path

    def _resolve_nmap(self):

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

    def collect(self, targets):

        nmap = self._resolve_nmap()

        if not nmap:
            raise CollectorError(
                "Nmap no está instalado o no se encontró en config/PATH."
            )

        # aceptar str o lista
        if isinstance(targets, str):
            targets = [targets]

        if not targets:
            raise CollectorError("No targets provided to Nmap")

        try:

            cmd = [
                nmap,
                "-sV",
                "-Pn",
                "--top-ports", "1000",
                "-oX", "-"
            ] + targets

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                raise CollectorError(f"Nmap execution failed: {result.stderr}")

            return result.stdout

        except subprocess.TimeoutExpired:
            raise CollectorError("Nmap timeout")

        except Exception as e:
            raise CollectorError(f"Nmap error: {e}")