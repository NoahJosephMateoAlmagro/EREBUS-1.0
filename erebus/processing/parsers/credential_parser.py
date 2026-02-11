import re

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

    JSON_USER_KEYS = {"user", "username", "login"}
    JSON_PASS_KEYS = {"password", "pwd", "pass"}
    JSON_TOKEN_KEYS = {"apikey", "api_key", "token", "secret"}

    def parse(self, text: str, source: str):
        results = []
        seen = set()

        if not text:
            return results

        for _, _, value in USER_REGEX.findall(text):
            item = ("user", value, source)
            if item not in seen:
                results.append(item)
                seen.add(item)

        for _, _, value in PASS_REGEX.findall(text):
            item = ("password", value, source)
            if item not in seen:
                results.append(item)
                seen.add(item)

        for _, value in TOKEN_REGEX.findall(text):
            item = ("token", value, source)
            if item not in seen:
                results.append(item)
                seen.add(item)

        return results

    def parse_json(self, obj, source: str):
        results = []
        seen = set()

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    key = k.lower()
                    if isinstance(v, str):
                        if key in self.JSON_USER_KEYS:
                            t = "user"
                        elif key in self.JSON_PASS_KEYS:
                            t = "password"
                        elif key in self.JSON_TOKEN_KEYS:
                            t = "token"
                        else:
                            t = None

                        if t:
                            item = (t, v, source)
                            if item not in seen:
                                results.append(item)
                                seen.add(item)

                    walk(v)

            elif isinstance(o, list):
                for i in o:
                    walk(i)

        walk(obj)
        return results


