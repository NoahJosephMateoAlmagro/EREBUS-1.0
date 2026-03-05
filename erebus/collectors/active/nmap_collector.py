import subprocess
import shutil
from pathlib import Path
from collectors.base import Collector
from exceptions.exceptions import CollectorError

class NmapCollector(Collector):

    def __init__(self, timeout: int = 60, nmap_path: str | None = None):
        self.timeout = timeout
        self.nmap_path = nmap_path

    def _resolve_nmap(self):

        # primero se mira en config
        if self.nmap_path and Path(self.nmap_path).exists():
            return self.nmap_path

        # 2se comprueba si existe nmap PATH
        path = shutil.which("nmap")
        if path:
            return path

        # rutas típicas Windows si no existe
        candidates = [
            r"C:\\Program Files\\Nmap\\nmap.exe",
            r"C:\\Program Files (x86)\\Nmap\\nmap.exe"
        ]

        for p in candidates:
            if Path(p).exists():
                return p

        return None

    def collect(self, target: str):

        nmap = self._resolve_nmap()

        if not nmap:
            raise CollectorError(
                "Nmap no está instalado o no se encontró en config/PATH."
            )

        try:

            cmd = [
                nmap,
                "-sV",
                "-Pn",
                "--top-ports", "1000",
                "-oX", "-",
                target
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                raise CollectorError(f"Nmap execution failed for {target}")

            return result.stdout

        except subprocess.TimeoutExpired:
            raise CollectorError(f"Nmap timeout for {target}")

        except Exception as e:
            raise CollectorError(f"Nmap error for {target}: {e}")