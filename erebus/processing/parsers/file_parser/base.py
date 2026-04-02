from abc import ABC, abstractmethod


class BaseFileParser(ABC):
    """
    Base class for all file parsers.

    Each parser must define:
    - supported file extensions
    - extraction logic for text content
    """

    technique: str = None
    extensions: set[str] = set()

    def can_parse(self, url: str) -> bool:
        """
        Determines whether the parser supports the given URL.

        Args:
            url (str): File URL

        Returns:
            bool: True if supported, False otherwise
        """
        return url.lower().endswith(tuple(self.extensions))

    @abstractmethod
    def extract_text(self, content: bytes) -> str:
        """
        Extracts text content from raw file bytes.

        Args:
            content (bytes): Raw file content

        Returns:
            str: Extracted text
        """
        pass

    def parse(self, url: str, content: bytes) -> str:
        """
        Default parsing entry point.

        Args:
            url (str): File URL
            content (bytes): Raw file content

        Returns:
            str: Extracted text
        """
        return self.extract_text(content)