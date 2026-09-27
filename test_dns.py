import dns.resolver

domain = "google.com"

answer = dns.resolver.resolve(domain, "A")

for ip in answer:
    print("IP Address:", ip)