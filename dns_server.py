import socket
import dns.resolver
import time


HOST = "127.0.0.1"
PORT = 5000


cache = {}

MAX_CACHE_SIZE = 10
MIN_CACHE_SIZE = 3
MAX_ALLOWED_CACHE_SIZE = 20

ADAPTIVE_WINDOW_SIZE = 10

LOW_HIT_RATIO = 30.0
HIGH_HIT_RATIO = 75.0

adaptive_queries = 0
adaptive_hits = 0


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
    global adaptive_queries
    global adaptive_hits

    total_queries += 1

    current_time = time.time()

    # --------------------------------------------------
    # CHECK CACHE
    # --------------------------------------------------

    if domain in cache:

        cache_entry = cache[domain]

        # Check whether TTL is still valid
        if current_time < cache_entry["expiry"]:

            cache_hits += 1

            adaptive_queries += 1
            adaptive_hits += 1

            # Increase popularity count
            cache_entry["frequency"] += 1

            # Update last access time
            cache_entry["last_access"] = current_time

            remaining_ttl = (
                cache_entry["expiry"]
                - current_time
            )

            return (
                "CACHE HIT\n"
                "Domain: " + domain + "\n"
                "IP Address: "
                + cache_entry["ip"]
                + "\n"
                "TTL Remaining: "
                "{:.2f} seconds".format(
                    remaining_ttl
                )
            )

        else:

            # Remove expired entry
            del cache[domain]

    # --------------------------------------------------
    # CACHE MISS
    # --------------------------------------------------

    cache_misses += 1
    dns_queries += 1

    adaptive_queries += 1

    try:

        start_time = time.time()

        answer = dns.resolver.resolve(
            domain,
            "A"
        )

        end_time = time.time()

        response_time = (
            (end_time - start_time)
            * 1000
        )

        total_dns_response_time += (
            response_time
        )

        ip_address = str(answer[0])

        actual_ttl = answer.rrset.ttl

        expiry_time = (
            time.time()
            + actual_ttl
        )

        # --------------------------------------------------
        # INTELLIGENT CACHE REPLACEMENT
        # --------------------------------------------------

        if len(cache) >= MAX_CACHE_SIZE:

            domain_to_remove = (
                select_cache_entry_for_replacement()
            )

            if domain_to_remove is not None:

                del cache[
                    domain_to_remove
                ]

        # --------------------------------------------------
        # ADD NEW CACHE ENTRY
        # --------------------------------------------------

        cache[domain] = {

            "ip": ip_address,

            "ttl": actual_ttl,

            "expiry": expiry_time,

            # Number of times the domain
            # has been requested
            "frequency": 1,

            # Most recent access time
            "last_access": time.time(),

            # Time when cache entry was created
            "created_at": time.time()
        }

        return (
            "CACHE MISS\n"
            "Domain: " + domain + "\n"
            "IP Address: "
            + ip_address
            + "\n"
            "Response Time: "
            "{:.2f} ms\n".format(
                response_time
            )
            + "TTL: "
            + str(actual_ttl)
            + " seconds"
        )

    except Exception as e:

        return (
            "DNS resolution failed: "
            + str(e)
        )



def adapt_cache_size():

    global MAX_CACHE_SIZE
    global adaptive_queries
    global adaptive_hits

    # Wait until one evaluation window is complete
    if adaptive_queries < ADAPTIVE_WINDOW_SIZE:
        return None

    hit_ratio = (
        adaptive_hits / adaptive_queries
    ) * 100

    print(
        "Adaptive evaluation:",
        adaptive_queries,
        "requests, hit_ratio:",
        round(hit_ratio, 2),
        "%"
    )

    old_size = MAX_CACHE_SIZE

    # Increase capacity when cache performance is high
    if hit_ratio > HIGH_HIT_RATIO:

        MAX_CACHE_SIZE = min(
            MAX_CACHE_SIZE + 2,
            MAX_ALLOWED_CACHE_SIZE
        )

    # Reduce capacity when cache performance is low
    elif hit_ratio < LOW_HIT_RATIO:

        MAX_CACHE_SIZE = max(
            MAX_CACHE_SIZE - 2,
            MIN_CACHE_SIZE
        )

    # Reset the evaluation window
    adaptive_queries = 0
    adaptive_hits = 0

    if MAX_CACHE_SIZE != old_size:

        print(
            "Adaptive cache size changed:",
            old_size,
            "->",
            MAX_CACHE_SIZE,
            "| Hit ratio:",
            round(hit_ratio, 2),
            "%"
        )

        # Remove entries if the cache exceeds the new capacity
        while len(cache) > MAX_CACHE_SIZE:

            domain_to_remove = (
                select_cache_entry_for_replacement()
            )

            if domain_to_remove is None:
                break

            del cache[domain_to_remove]

        return (
            "Cache size changed from "
            + str(old_size)
            + " to "
            + str(MAX_CACHE_SIZE)
        )

    return None


def select_cache_entry_for_replacement():

    current_time = time.time()

    # Remove expired entries first
    for domain, entry in list(cache.items()):

        if current_time >= entry["expiry"]:
            del cache[domain]

    # If removing expired entries created space,
    # no additional replacement is needed.
    if len(cache) < MAX_CACHE_SIZE:
        return None

    scores = {}

    for domain, entry in cache.items():

        # Popularity: more requests means more useful
        frequency = entry["frequency"]
        popularity_score = frequency / (frequency + 1)

        # Recency: recently accessed entries score higher
        age = current_time - entry["last_access"]
        recency_score = 1 / (1 + age)

        # TTL: longer remaining lifetime scores higher
        remaining_ttl = max(
            0,
            entry["expiry"] - current_time
        )

        ttl_score = remaining_ttl / (
            remaining_ttl + 60
        )

        # Combine normalized scores
        score = (
            0.5 * popularity_score
            + 0.3 * recency_score
            + 0.2 * ttl_score
        )

        scores[domain] = score



    # Evict the entry with the lowest score
    if scores:
        return min(scores, key=scores.get)

    return None



def get_statistics():

    result = "\n"

    result += (
        "===================================\n"
    )

    result += (
        "       DNS RESOLVER STATISTICS\n"
    )

    result += (
        "===================================\n"
    )

    result += (
        "Total Queries: "
        + str(total_queries)
        + "\n"
    )

    result += (
        "Cache Hits: "
        + str(cache_hits)
        + "\n"
    )

    result += (
        "Cache Misses: "
        + str(cache_misses)
        + "\n"
    )

    result += (
        "DNS Queries Sent: "
        + str(dns_queries)
        + "\n"
    )

    if total_queries > 0:

        hit_ratio = (
            cache_hits
            / total_queries
        ) * 100

        result += (
            "Cache Hit Ratio: "
            "{:.2f}%\n".format(
                hit_ratio
            )
        )

    if dns_queries > 0:

        average_time = (
            total_dns_response_time
            / dns_queries
        )

        result += (
            "Average DNS Response Time: "
            "{:.2f} ms\n".format(
                average_time
            )
        )

    result += (
        "Cache Size: "
        + str(len(cache))
        + "\n"
    )

    result += (
        "Maximum Cache Size: "
        + str(MAX_CACHE_SIZE)
        + "\n"
    )

    result += (
        "==================================="
    )

    return result


def get_cache_contents():

    current_time = time.time()

    result = "\n"

    result += (
        "===================================\n"
    )

    result += (
        "          CACHE CONTENTS\n"
    )

    result += (
        "===================================\n"
    )

    if len(cache) == 0:

        result += (
            "Cache is empty\n"
        )

    else:

        for domain, entry in cache.items():

            remaining_ttl = (
                entry["expiry"]
                - current_time
            )

            if remaining_ttl < 0:

                remaining_ttl = 0

            result += (
                "Domain: "
                + domain
                + "\n"
            )

            result += (
                "IP Address: "
                + entry["ip"]
                + "\n"
            )

            result += (
                "Frequency: "
                + str(entry["frequency"])
                + "\n"
            )

            result += (
                "TTL Remaining: "
                "{:.2f} seconds\n".format(
                    remaining_ttl
                )
            )

            result += (
                "Last Access: "
                + time.strftime(
                    "%H:%M:%S",
                    time.localtime(
                        entry["last_access"]
                    )
                )
                + "\n"
            )

            result += (
                "-----------------------------------\n"
            )

    result += (
        "==================================="
    )

    return result


# --------------------------------------------------
# CREATE UDP SOCKET
# --------------------------------------------------

server_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)


server_socket.bind(
    (HOST, PORT)
)


print(
    "DNS Resolver Server started"
)

print(
    "Listening on",
    HOST,
    "port",
    PORT
)

print(
    "Maximum Cache Size:",
    MAX_CACHE_SIZE
)


# --------------------------------------------------
# MAIN SERVER LOOP
# --------------------------------------------------

while True:

    data, client_address = (
        server_socket.recvfrom(1024)
    )

    request = (
        data.decode()
        .strip()
    )

    print(
        "\nRequest received:",
        request
    )

    # --------------------------------------------------
    # STATISTICS COMMAND
    # --------------------------------------------------

    if request.lower() == "stats":

        response = get_statistics()

    # --------------------------------------------------
    # CACHE CONTENTS COMMAND
    # --------------------------------------------------

    elif request.lower() == "cache":

        response = get_cache_contents()

    # --------------------------------------------------
    # CLEAR CACHE COMMAND
    # --------------------------------------------------

    elif request.lower() == "clear":

        cache.clear()

        response = (
            "Cache cleared successfully"
        )

    # --------------------------------------------------
    # CHANGE CACHE SIZE
    # --------------------------------------------------

    elif request.lower().startswith("setsize "):

        try:

            new_size = int(
                request.split()[1]
            )

            if new_size <= 0:

                raise ValueError

            MAX_CACHE_SIZE = max(
                MIN_CACHE_SIZE,
                min(new_size, MAX_ALLOWED_CACHE_SIZE)
            )

            cache.clear()

            response = (
                "Maximum cache size set to "
                + str(MAX_CACHE_SIZE)
            )

        except Exception as e:
            print("Setsize error:" , repr(e))
            response = "Invalid cache size : " + str(e)




    # --------------------------------------------------
    # DNS REQUEST
    # --------------------------------------------------

    else:

        response = resolve_domain(
            request
        )
    # --------------------------------------------------
    # SEND RESPONSE
    # --------------------------------------------------

    server_socket.sendto(
        response.encode(),
        client_address
    )

    if request.lower() not in (
        "stats",
        "cache",
        "clear"
    ) and not request.lower().startswith("setsize"):

      adapt_cache_size()
