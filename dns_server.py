import socket
import dns.resolver
import time

HOST = "127.0.0.1"
PORT = 5000

cache = {}

# Maximum number of entries allowed in cache
MAX_CACHE_SIZE = 10

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

    # Check cache
    if domain in cache:

        cache_entry = cache[domain]

        # Check whether TTL has expired
        if current_time < cache_entry["expiry"]:

            cache_hits += 1

            remaining_ttl = cache_entry["expiry"] - current_time

            return (
                "CACHE HIT\n"
                "Domain: " + domain + "\n"
                "IP Address: " + cache_entry["ip"] + "\n"
                "TTL Remaining: {:.2f} seconds".format(
                    remaining_ttl
                )
            )

        else:

            # Remove expired entry
            del cache[domain]

    # Cache MISS
    cache_misses += 1
    dns_queries += 1

    try:

        start_time = time.time()

        answer = dns.resolver.resolve(
            domain,
            "A"
        )

        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        total_dns_response_time += response_time

        ip_address = str(answer[0])

        # Get actual DNS TTL
        actual_ttl = answer.rrset.ttl

        expiry_time = time.time() + actual_ttl

        # If cache is full, remove oldest entry
        if len(cache) >= MAX_CACHE_SIZE:

            oldest_domain = next(iter(cache))

            del cache[oldest_domain]

        # Store new entry
        cache[domain] = {
            "ip": ip_address,
            "ttl": actual_ttl,
            "expiry": expiry_time
        }

        return (
            "CACHE MISS\n"
            "Domain: " + domain + "\n"
            "IP Address: " + ip_address + "\n"
            "Response Time: {:.2f} ms\n".format(
                response_time
            )
            + "TTL: "
            + str(actual_ttl)
            + " seconds"
        )

    except Exception as e:

        return "DNS resolution failed: " + str(e)


def get_statistics():

    result = "\n"
    result += "===================================\n"
    result += "       DNS RESOLVER STATISTICS\n"
    result += "===================================\n"

    result += "Total Queries: " + str(total_queries) + "\n"
    result += "Cache Hits: " + str(cache_hits) + "\n"
    result += "Cache Misses: " + str(cache_misses) + "\n"
    result += "DNS Queries Sent: " + str(dns_queries) + "\n"

    if total_queries > 0:

        hit_ratio = (
            cache_hits / total_queries
        ) * 100

        result += "Cache Hit Ratio: {:.2f}%\n".format(
            hit_ratio
        )

    if dns_queries > 0:

        average_time = (
            total_dns_response_time / dns_queries
        )

        result += "Average DNS Response Time: {:.2f} ms\n".format(
            average_time
        )

    result += "Cache Size: " + str(len(cache)) + "\n"
    result += "Maximum Cache Size: " + str(MAX_CACHE_SIZE) + "\n"

    result += "==================================="

    return result


# Create UDP socket
server_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)

server_socket.bind(
    (HOST, PORT)
)

print("DNS Resolver Server started")
print("Listening on", HOST, "port", PORT)
print("Maximum Cache Size:", MAX_CACHE_SIZE)

while True:

    data, client_address = server_socket.recvfrom(1024)

    request = data.decode().strip()

    print("\nRequest received:", request)

    if request.lower() == "stats":

        response = get_statistics()

    elif request.lower() == "clear":

        cache.clear()

        response = "Cache cleared successfully"

    elif request.lower().startswith("setsize "):

        try:

            MAX_CACHE_SIZE = int(
                request.split()[1]
            )

            cache.clear()

            response = (
                "Maximum cache size set to "
                + str(MAX_CACHE_SIZE)
            )

        except:

            response = "Invalid cache size"

    else:

        response = resolve_domain(request)

    server_socket.sendto(
        response.encode(),
        client_address
    )