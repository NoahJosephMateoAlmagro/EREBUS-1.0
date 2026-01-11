from collectors.passive.js_parser import JSParser

parser = JSParser()

result = parser.parse(
    "https://www.urjc.es/js/main.js"
)

print(result)
