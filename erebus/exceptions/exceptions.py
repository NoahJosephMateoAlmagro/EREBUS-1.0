class ErebusError(Exception):
    """
    Base exception for the EREBUS engine.
    """
    pass


class CollectorError(ErebusError):
    """
    Exception raised when a collector fails.
    """
    pass


class AnalyzerError(ErebusError):
    """
    Exception raised when an analyzer fails to process data.
    """
    pass


class ConfigurationError(ErebusError):
    """
    Exception raised when there is a configuration issue.
    """
    pass