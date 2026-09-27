import dns.resolver
import time

def resolve_domain(domain):
    start_time = time.time()

    try:
        answer = dns.resolver.resolve(domain, "A")

        end_time = time.time()
        response_time = (end_time - start_time) * 1000

        print("\nDomain:", domain)

        for ip in answer:
            print("IP Address:", ip)

        print("Response Time: {:.2f} ms".format(response_time))

    except Exception as e:
        print("DNS resolution failed:", e)


domain = input("Enter domain name: ")
resolve_domain(domain)