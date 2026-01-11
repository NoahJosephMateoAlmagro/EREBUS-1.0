from collectors.passive.waybackMachine import WaybackCollector

wb = WaybackCollector(timeout=10, limit=50)
urls = wb.collect("urjc.es")
print(len(urls))

