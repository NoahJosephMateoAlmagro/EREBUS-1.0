from collectors.passive.APIs.shodan_collector import ShodanCollector

API_KEY = "TU_API_KEY"

collector = ShodanCollector()
collector.set_api_key(API_KEY)

host = collector.get_host("8.8.8.8")

print(host)