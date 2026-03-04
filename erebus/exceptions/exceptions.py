class ErebusError(Exception):
    """Excepción base del motor EREBUS."""
    pass


class CollectorError(ErebusError):
    """Error al ejecutar un collector."""
    pass


class AnalyzerError(ErebusError):
    """Error al procesar datos en un analyzer."""
    pass


class ConfigurationError(ErebusError):
    """Error en la configuración del motor."""
    pass