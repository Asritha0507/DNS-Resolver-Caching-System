import dns.resolver
import time

cache = {}

# Statistics
total_queries = 0
cache_hits = 0
cache_misses = 0
dns_queries = 0
total_dns_response_time = 0


def resolve_domain(domain):

    global total_queries
    global cache_hits
    global cache_misses
    global dns_queries
    global total_dns_response_time

    total_queries += 1

    current_time = time.time()

    # Check if domain exists in cache
    if domain in cache:

        cache_entry = cache[domain]

        # Check if cache is still valid
        if current_time < cache_entry["expiry"]:

            cache_hits += 1

            print("\nCache HIT")
            print("Domain:", domain)
            print("IP Address:", cache_entry["ip"])

            remaining_ttl = cache_entry["expiry"] - current_time
            print("TTL Remaining: {:.2f} seconds".format(remaining_ttl))

            return

        else:
            print("\nCache EXPIRED")
            del cache[domain]

    # Cache MISS
    cache_misses += 1
    dns_queries += 1

    print("\nCache MISS")

    start_time = time.time()

    try:
        answer = dns.resolver.resolve(domain, "A")

        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        total_dns_response_time += response_time

        # Get IP address
        ip_address = str(answer[0])

        # Get actual TTL
        actual_ttl = answer.rrset.ttl

        # Calculate expiry time
        expiry_time = time.time() + actual_ttl

        # Store in cache
        cache[domain] = {
            "ip": ip_address,
            "ttl": actual_ttl,
            "expiry": expiry_time
        }

        print("Domain:", domain)
        print("IP Address:", ip_address)
        print("Response Time: {:.2f} ms".format(response_time))
        print("Actual TTL:", actual_ttl, "seconds")

    except Exception as e:
        print("DNS resolution failed:", e)


def show_statistics():

    print("\n")
    print("=" * 35)
    print("       DNS RESOLVER STATISTICS")
    print("=" * 35)

    print("Total Queries:", total_queries)
    print("Cache Hits:", cache_hits)
    print("Cache Misses:", cache_misses)
    print("DNS Queries Sent:", dns_queries)

    if total_queries > 0:
        hit_ratio = (cache_hits / total_queries) * 100
        print("Cache Hit Ratio: {:.2f}%".format(hit_ratio))

    if dns_queries > 0:
        average_time = total_dns_response_time / dns_queries
        print("Average DNS Response Time: {:.2f} ms".format(average_time))

    print("=" * 35)


while True:

    domain = input(
        "\nEnter domain name "
        "(or 'stats' for statistics, 'exit' to stop): "
    )

    if domain.lower() == "exit":
        break

    elif domain.lower() == "stats":
        show_statistics()
        continue

    resolve_domain(domain)