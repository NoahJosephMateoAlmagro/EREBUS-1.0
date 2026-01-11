from collectors.passive.js_parser import JSParser

parser = JSParser()

parsed = parser.parse(
    "http://localhost:8000/test.js",
    "localhost"
)

print(parsed)

from collectors.passive.credential_parser import CredentialParser

cred = CredentialParser()
creds = cred.parse(parsed["raw"], source="js")

print(creds)
