import socket
import dns.resolver
import time


HOST = "127.0.0.1"
PORT = 5000


cache = {}

MAX_CACHE_SIZE = 10


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

    # --------------------------------------------------
    # CHECK CACHE
    # --------------------------------------------------

    if domain in cache:

        cache_entry = cache[domain]

        # Check whether TTL is still valid
        if current_time < cache_entry["expiry"]:

            cache_hits += 1

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


def select_cache_entry_for_replacement():

    current_time = time.time()

    worst_domain = None

    worst_score = float("inf")

    # --------------------------------------------------
    # CALCULATE SCORE FOR EACH CACHE ENTRY
    # --------------------------------------------------

    for domain, entry in cache.items():

        # Remaining TTL
        remaining_ttl = (
            entry["expiry"]
            - current_time
        )

        if remaining_ttl < 0:

            remaining_ttl = 0

        # Time since last access
        age = (
            current_time
            - entry["last_access"]
        )

        # Number of requests
        frequency = entry["frequency"]

        # --------------------------------------------------
        # POPULARITY SCORE
        # --------------------------------------------------

        popularity_score = frequency

        # --------------------------------------------------
        # RECENCY SCORE
        # --------------------------------------------------

        recency_score = (
            1 / (1 + age)
        )

        # --------------------------------------------------
        # TTL SCORE
        # --------------------------------------------------

        ttl_score = remaining_ttl

        # --------------------------------------------------
        # COMBINED INTELLIGENT SCORE
        # --------------------------------------------------

        score = (

            (0.5 * popularity_score)

            + (0.3 * recency_score)

            + (0.2 * ttl_score)

        )

        # Lower score means the entry
        # is less useful to keep.

        if score < worst_score:

            worst_score = score

            worst_domain = domain

    return worst_domain


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

    elif request.lower().startswith(
        "setsize "
    ):

        try:

            new_size = int(
                request.split()[1]
            )

            if new_size <= 0:

                raise ValueError

            MAX_CACHE_SIZE = new_size

            cache.clear()

            response = (
                "Maximum cache size set to "
                + str(MAX_CACHE_SIZE)
            )

        except:

            response = (
                "Invalid cache size"
            )

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