import re
from typing import Any, List, Tuple


USER_REGEX = re.compile(
    r"\b(user(name)?|login)[\w\-]*\s*=\s*['\"]([^'\"\s]{3,})['\"]",
    re.IGNORECASE
)

PASS_REGEX = re.compile(
    r"\b(pass(word)?|pwd)[\w\-]*\s*=\s*['\"]([^'\"\s]{3,})['\"]",
    re.IGNORECASE
)

TOKEN_REGEX = re.compile(
    r"\b(api[_-]?key|token|secret)[\w\-]*\s*=\s*['\"]([^'\"\s]{8,})['\"]",
    re.IGNORECASE
)


class CredentialParser:
    """
    Parser responsible for extracting credentials from raw text and JSON structures.
    Supports detection of users, passwords and tokens.
    """

    JSON_USER_KEYS = {"user", "username", "login"}
    JSON_PASS_KEYS = {"password", "pwd", "pass"}
    JSON_TOKEN_KEYS = {"apikey", "api_key", "token", "secret"}

    def parse(self, text: str, source: str) -> List[Tuple[str, str, str]]:
        """
        Extracts credentials from raw text using regex patterns.

        Args:
            text (str): Input text
            source (str): Source label for extracted credentials

        Returns:
            list[tuple[str, str, str]]: Extracted credentials
        """
        results = []
        seen = set()

        if not text:
            return results

        for _, _, value in USER_REGEX.findall(text):
            self._add_result(results, seen, ("user", value, source))

        for _, _, value in PASS_REGEX.findall(text):
            self._add_result(results, seen, ("password", value, source))

        for _, value in TOKEN_REGEX.findall(text):
            self._add_result(results, seen, ("token", value, source))

        return results

    def parse_json(self, obj: Any, source: str) -> List[Tuple[str, str, str]]:
        """
        Recursively extracts credentials from JSON-like structures.

        Args:
            obj (Any): JSON object (dict or list)
            source (str): Source label for extracted credentials

        Returns:
            list[tuple[str, str, str]]: Extracted credentials
        """
        results = []
        seen = set()

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    key = k.lower()

                    if isinstance(v, str):
                        credential_type = self._classify_json_key(key)

                        if credential_type:
                            self._add_result(results, seen, (credential_type, v, source))

                    walk(v)

            elif isinstance(o, list):
                for item in o:
                    walk(item)

        walk(obj)
        return results

    def _classify_json_key(self, key: str) -> str | None:
        """
        Determines credential type based on JSON key.

        Args:
            key (str): JSON key

        Returns:
            str | None: Credential type or None
        """
        if key in self.JSON_USER_KEYS:
            return "user"
        if key in self.JSON_PASS_KEYS:
            return "password"
        if key in self.JSON_TOKEN_KEYS:
            return "token"
        return None

    def _add_result(self, results, seen, item):
        """
        Adds a credential result if not already seen.

        Args:
            results: Result list
            seen: Deduplication set
            item: Credential tuple
        """
        if item not in seen:
            results.append(item)
            seen.add(item)