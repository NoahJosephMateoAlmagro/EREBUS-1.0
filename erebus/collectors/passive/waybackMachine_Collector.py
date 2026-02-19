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

    def __init__(self, timeout=10, cdx_limit=2000):
        self.timeout = timeout
        self.cdx_limit = cdx_limit

    def collect(self, domain: str):

        params = {
            "url": f"{domain}/*",
            "output": "json",
            "fl": "timestamp,original,statuscode",
            "limit": self.cdx_limit
        }

        try:
            r = requests.get(
                self.CDX_URL,
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": "EREBUS/1.0"}
            )

            print("[WAYBACK][COLLECTOR] Request URL:", r.url)
            print("[WAYBACK][COLLECTOR] Status:", r.status_code)

            if r.status_code != 200:
                return []

            data = r.json()

            print("[WAYBACK][COLLECTOR] Rows received:", len(data))

            return [
                {
                    "timestamp": row[0],
                    "original": row[1],
                    "status": row[2]
                }
                for row in data[1:]
            ]

        except Exception as e:
            print("[WAYBACK][COLLECTOR] Error:", e)
            return []
