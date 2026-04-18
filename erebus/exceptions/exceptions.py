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


class DatabaseError(ErebusError):
    """
    Exception raised when a database operation fails.
    """
    pass


class ConfigurationError(ErebusError):
    """
    Exception raised when there is a configuration issue.
    """
    pass

class ParserError(ErebusError):
    """
    Exception raised when a parser fails to process input data.
    """
    pass