class PassiveCollector:
    """
    Base class for passive collectors.
    All collectors must implement collect(target)
    and return a list or dict with collected data.
    """
    def collect(self, target: str):
        raise NotImplementedError("PassiveCollector subclasses must implement collect()")
