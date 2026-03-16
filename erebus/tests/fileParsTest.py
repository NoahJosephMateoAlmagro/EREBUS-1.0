from application.services.file_parsing_service import FileParsingService

parser = FileParsingService()

url = "https://arxiv.org/pdf/1706.03762.pdf"

result = parser.parse(url)

print(result["technique"])
print(len(result["text"]))