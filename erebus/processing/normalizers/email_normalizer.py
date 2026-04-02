import re
import base64
import html


class EmailAnalyzer:
    """
    Analyzer responsible for extracting and normalizing email addresses
    from raw text using multiple detection techniques.
    """

    EMAIL_REGEX = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    )

    OBFUSCATED_PATTERNS = [
        (r"\s*\[\s*at\s*\]\s*", "@"),
        (r"\s*\(\s*at\s*\)\s*", "@"),
        (r"\s+at\s+", "@"),
        (r"\s*\[\s*dot\s*\]\s*", "."),
        (r"\s*\(\s*dot\s*\)\s*", "."),
        (r"\s+dot\s+", "."),
    ]

    CONCAT_REGEX = re.compile(
        r"['\"]([a-zA-Z0-9._%+-]+)['\"]\s*\+\s*['\"]@['\"]\s*\+\s*['\"]([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})['\"]"
    )

    BASE64_CALL_REGEX = re.compile(
        r"atob\(\s*['\"]([A-Za-z0-9+/=]{20,})['\"]\s*\)"
    )

    BASE64_TOKEN_REGEX = re.compile(
        r"\b[A-Za-z0-9+/=]{24,}\b"
    )

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def extract(self, text: str) -> set[str]:
        """
        Extracts email addresses using multiple techniques:
        - Plain text emails
        - Obfuscations ([at], [dot])
        - JavaScript concatenation
        - HTML entities and escapes
        - Base64 decoding
        """
        found = set()

        if not text:
            return found

        lowered = text.lower()

        # Plain emails
        for e in self.EMAIL_REGEX.findall(lowered):
            found.add(e)

        # Obfuscation replacement
        candidate = lowered
        for pattern, repl in self.OBFUSCATED_PATTERNS:
            candidate = re.sub(pattern, repl, candidate)

        for e in self.EMAIL_REGEX.findall(candidate):
            found.add(e)

        # JS concatenation patterns
        for user, domain in self.CONCAT_REGEX.findall(text):
            email = f"{user}@{domain}".lower()
            if self.EMAIL_REGEX.match(email):
                found.add(email)

        # HTML entities and JS escapes
        unescaped = html.unescape(text)

        try:
            unescaped = unescaped.encode().decode("unicode_escape")
        except Exception:
            pass

        for e in self.EMAIL_REGEX.findall(unescaped.lower()):
            found.add(e)

        # Base64 inside atob()
        for token in self.BASE64_CALL_REGEX.findall(text):
            self._decode_base64_email(token, found)

        # Raw Base64 tokens
        compact = re.sub(r"\s+", "", text)

        for token in self.BASE64_TOKEN_REGEX.findall(compact):
            self._decode_base64_email(token, found)

        return found

    def normalize(self, email: str) -> str | None:
        """
        Performs minimal normalization of an email address.
        """
        if not email:
            return None

        email = email.strip().lower()

        if "@" not in email:
            return None

        return email

    def extract_from_file_text(self, text: str) -> set[str]:
        """
        Semantic alias for file parsing context.
        """
        return self.extract(text)

    # -------------------------------------------------
    # Internal
    # -------------------------------------------------

    def _decode_base64_email(self, token: str, found: set[str]) -> None:
        try:
            decoded = base64.b64decode(token).decode("utf-8", errors="ignore")

            for e in self.EMAIL_REGEX.findall(decoded.lower()):
                found.add(e)

        except Exception:
            pass