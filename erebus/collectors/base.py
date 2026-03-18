class Collector:
    """
    Base class for passive collectors.
    All collectors must implement collect(target)
    and return a list or dict with collected data.
    """
    def __init__(self):
        self.name = self.__class__.__name__

    def collect(self, target: str):
        """
          Main collection method.

          Args:
              target (str): Target domain or entity
        """

        raise NotImplementedError("PassiveCollector subclasses must implement collect()")
