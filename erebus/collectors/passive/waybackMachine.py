import requests
from urllib.parse import urlparse
from collections import defaultdict

"""
[BORRAR DESPUES]

WAYBACK COLLECTOR – EXPLICACIÓN COMPLETA Y SIMPLIFICADA

Este módulo se encarga de recolectar URLs históricas de un dominio usando
Wayback Machine (Internet Archive), con el objetivo de analizar versiones
antiguas de páginas web y extraer información (emails, credenciales, etc.)
que ya no está disponible en la web actual.

-----------------------------------
PROBLEMA QUE SE QUIERE EVITAR
-----------------------------------

Wayback Machine almacena miles de snapshots por cada URL.
Si se analizaran todos:
- El programa sería lentísimo
- Aparecerían timeouts constantes
- El análisis no sería reproducible
- No sería defendible en un TFG

Por eso este módulo NO descarga todo, sino que:
- Filtra
- Deduplica
- Selecciona solo snapshots representativos

-----------------------------------
IDEA GENERAL DE FUNCIONAMIENTO
-----------------------------------

1) Consultar el API CDX de Wayback para obtener snapshots históricos
2) Filtrar resultados inútiles (no HTML, errores, recursos estáticos)
3) Agrupar snapshots por URL original
4) De cada URL distinta:
   - seleccionar SOLO el snapshot más antiguo
   - seleccionar SOLO el snapshot más reciente
5) Devolver una lista pequeña de URLs listas para el crawler

-----------------------------------
PARÁMETROS IMPORTANTES
-----------------------------------

- timeout:
  Tiempo máximo de espera al consultar el API de Wayback.
  Evita que el programa se quede bloqueado.

- limit:
  Número máximo de URLs históricas distintas que se van a procesar.
  NO es número de snapshots, sino número de URLs únicas.

- cdx_limit:
  Límite de resultados que se solicitan al API CDX antes de filtrar.
  Se usa como margen para poder aplicar filtros posteriores.

- min_year:
  Año mínimo aceptado para los snapshots.
  Evita analizar versiones demasiado antiguas o rotas.

-----------------------------------
FILTRADO DE URLs
-----------------------------------

Se descartan automáticamente:
- Recursos estáticos (css, js, imágenes, fuentes, zip, etc.)
- URLs sin esquema http/https
- Contenido técnico sin valor (pagespeed, media, etc.)

Esto reduce ruido y mejora el rendimiento.

-----------------------------------
SELECCIÓN DE SNAPSHOTS
-----------------------------------

Una misma URL puede tener cientos o miles de snapshots.
Analizarlos todos no aporta mucho valor adicional.

Por eso se seleccionan SOLO:
- El primer snapshot (primera aparición histórica)
- El último snapshot (versión histórica más reciente)

Esta decisión:
- Maximiza cobertura temporal
- Minimiza coste computacional
- Es fácil de justificar metodológicamente

-----------------------------------
RESULTADO FINAL
-----------------------------------

El método collect() devuelve una lista de URLs ya construidas
del tipo:

https://web.archive.org/web/{timestamp}/{url_original}

Estas URLs se pasan directamente al crawler,
que no necesita saber nada de Wayback internamente.

-----------------------------------
MANEJO DE ERRORES
-----------------------------------

- Si el API de Wayback no responde → se informa y se continúa
- Si hay timeout → se evita que el programa se bloquee
- Cualquier fallo no rompe la ejecución general

-----------------------------------
RESUMEN
-----------------------------------

Este módulo implementa una recolección histórica controlada,
priorizando estabilidad, rendimiento y reproducibilidad,
evitando análisis masivos innecesarios y manteniendo
un diseño limpio y justificable para un proyecto académico.

[BORRAR DESPUES]
"""

class WaybackCollector:

    CDX_URL = "https://web.archive.org/cdx/search/cdx"
    name = "wayback"

    BAD_EXTENSIONS = (
        ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
        ".woff", ".woff2", ".ttf", ".eot",
        ".zip", ".rar", ".7z"
    )

    def __init__(self, timeout=10, limit=50, cdx_limit = 2000,min_year=2008):
        self.timeout = timeout
        self.limit = limit
        self.cdx_limit = cdx_limit
        self.min_year = min_year

    def _is_valid_html_url(self, url: str) -> bool:
        url = url.lower()

        if ",a.media" in url or ".pagespeed." in url:
            return False

        parsed = urlparse(url)

        if not parsed.scheme.startswith("http"):
            return False

        for ext in self.BAD_EXTENSIONS:
            if parsed.path.endswith(ext):
                return False

        return True

    def _build_snapshot_url(self, timestamp, original):
        return f"https://web.archive.org/web/{timestamp}/{original}"

    def _select_snapshots(self, entries):
        """
        Selecciona snapshots representativos:
        - primero
        - último
        """
        entries = sorted(entries, key=lambda x: x["timestamp"])
        first = entries[0]
        last = entries[-1]

        print(
            f"[WAYBACK][DEBUG] Selección snapshots → "
            f"{first['timestamp']} / {last['timestamp']}"
        )

        snapshots = {first["snapshot"], last["snapshot"]}
        return list(snapshots)

    def collect(self, domain: str):
        """
        Devuelve URLs históricas distintas con snapshots representativos
        """
        urls = defaultdict(list)
        results = []

        params = {
            "url": f"*.{domain}/*",
            "output": "json",
            "fl": "timestamp,original,statuscode",
            "filter": "statuscode:200",
            "limit": self.cdx_limit,
            "collapse": "digest"
        }

        try:
            print(
                f"[WAYBACK][DEBUG] CDX query → "
                f"domain={domain} limit={self.cdx_limit} timeout={self.timeout}s"
            )

            r = requests.get(
                self.CDX_URL,
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": "EREBUS/1.0"}
            )

            if r.status_code in (502, 503, 504):
                print("[WAYBACK] API caída")
                return results

            if r.status_code != 200:
                return results

            data = r.json()

            # Saltar cabecera
            for row in data[1:]:
                timestamp, original, status = row
                year = int(timestamp[:4])

                if status != "200":
                    continue
                if year < self.min_year:
                    continue
                if not self._is_valid_html_url(original):
                    continue

                urls[original].append({
                    "timestamp": timestamp,
                    "year": year,
                    "snapshot": self._build_snapshot_url(timestamp, original)
                })

            # Limitar a URLs distintas
            for original in list(urls.keys())[:self.limit]:
                entries = urls[original]

                snapshots = self._select_snapshots(entries)

                for snapshot in snapshots:
                    results.append({
                        "url": snapshot,
                        "source": "wayback"
                    })

            for i, original in enumerate(list(urls.keys())[:self.limit], start=1):
                entries = urls[original]
                print(
                    f"[WAYBACK][DEBUG] ({i}) {original} "
                    f"→ snapshots totales: {len(entries)}"
                )

            print(f"[WAYBACK][DEBUG] URLs únicas detectadas: {len(urls)}")

        except requests.exceptions.ReadTimeout:
            print("[WAYBACK] Timeout alcanzado consultando CDX")
            return results

        except requests.exceptions.RequestException as e:
            print(f"[WAYBACK] Error de conexión: {e}")

        except Exception as e:
            print(f"[WAYBACK] Error inesperado: {e}")

        return results

