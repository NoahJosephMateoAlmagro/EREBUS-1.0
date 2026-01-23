from collectors.passive.DNS_Details.DNS_MX_Collector import DNS_MX_Collector
from collectors.passive.DNS_Details.DNS_TXT_Collector import DNS_TXT_Collector

mx = DNS_MX_Collector()
txt = DNS_TXT_Collector()

domain = "google.com"

print("=== MX ===")
mx_results = mx.collect(domain)
for r in mx_results:
    print(r)

print("\n=== TXT ===")
txt_results = txt.collect(domain)
for r in txt_results:
    print(r)
