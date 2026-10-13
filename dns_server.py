import socket
import time
import dns.resolver


# --------------------------------------------------
# SERVER CONFIGURATION
# --------------------------------------------------

HOST = "127.0.0.1"
PORT = 5000

MIN_CACHE_SIZE = 3
MAX_CACHE_SIZE = 10
MAX_ALLOWED_CACHE_SIZE = 20

ADAPTIVE_WINDOW_SIZE = 10
LOW_HIT_RATIO = 30.0
HIGH_HIT_RATIO = 75.0

cache = {}

adaptive_queries = 0
adaptive_hits = 0

total_queries = 0
cache_hits = 0
cache_misses = 0
dns_queries = 0
total_dns_response_time = 0.0


# --------------------------------------------------
# CACHE HELPERS
# --------------------------------------------------

def remove_expired_entries():
    """Remove entries whose DNS TTL has expired."""
    current_time = time.time()

    expired_domains = [
        domain
        for domain, entry in cache.items()
        if current_time >= entry["expiry"]
    ]

    for domain in expired_domains:
        del cache[domain]

    return len(expired_domains)


def select_cache_entry_for_replacement():
    """
    Select the least useful entry using popularity,
    recency, and remaining TTL.
    """
    remove_expired_entries()

    if not cache:
        return None

    current_time = time.time()
    scores = {}

    for domain, entry in cache.items():
        frequency = entry["frequency"]
        popularity_score = frequency / (frequency + 1)

        age = max(
            0.0,
            current_time - entry["last_access"]
        )
        recency_score = 1 / (1 + age)

        remaining_ttl = max(
            0.0,
            entry["expiry"] - current_time
        )
        ttl_score = remaining_ttl / (remaining_ttl + 60)

        # Higher score means the entry is more valuable.
        scores[domain] = (
            0.5 * popularity_score
            + 0.3 * recency_score
            + 0.2 * ttl_score
        )

    if scores:
        return min(scores, key=scores.get)

    return None


def make_room_for_entry():
    """Keep the cache within the current maximum size."""
    remove_expired_entries()

    while len(cache) >= MAX_CACHE_SIZE:
        domain_to_remove = (
            select_cache_entry_for_replacement()
        )

        if domain_to_remove is None:
            break

        print(
            "Cache replacement: evicting",
            domain_to_remove
        )
        del cache[domain_to_remove]


def add_to_cache(domain, ip_address, actual_ttl):
    """Insert a successful DNS result into the cache."""
    make_room_for_entry()

    now = time.time()

    cache[domain] = {
        "ip": ip_address,
        "ttl": actual_ttl,
        "expiry": now + actual_ttl,
        "frequency": 1,
        "last_access": now,
        "created_at": now
    }


# --------------------------------------------------
# DNS RESOLUTION
# --------------------------------------------------

def resolve_domain(domain):
    global total_queries
    global cache_hits
    global cache_misses
    global dns_queries
    global total_dns_response_time
    global adaptive_queries
    global adaptive_hits

    domain = domain.strip().lower().rstrip(".")

    if not domain:
        return "DNS resolution failed: domain name is empty"

    total_queries += 1
    current_time = time.time()

    # Check cache
    cache_entry = cache.get(domain)

    if cache_entry is not None:
        if current_time < cache_entry["expiry"]:
            cache_hits += 1
            adaptive_queries += 1
            adaptive_hits += 1

            cache_entry["frequency"] += 1
            cache_entry["last_access"] = current_time

            remaining_ttl = (
                cache_entry["expiry"] - current_time
            )

            return (
                "CACHE HIT\n"
                f"Domain: {domain}\n"
                f"IP Address: {cache_entry['ip']}\n"
                f"TTL Remaining: {remaining_ttl:.2f} seconds"
            )

        # Remove expired entry
        del cache[domain]

    # Cache miss
    cache_misses += 1
    dns_queries += 1
    adaptive_queries += 1

    try:
        start_time = time.time()

        answer = dns.resolver.resolve(domain, "A")

        end_time = time.time()

        response_time = (end_time - start_time) * 1000
        total_dns_response_time += response_time

        ip_address = str(answer[0])
        actual_ttl = int(answer.rrset.ttl)

        # Cache only records with a positive TTL
        if actual_ttl > 0:
            add_to_cache(domain, ip_address, actual_ttl)

        return (
            "CACHE MISS\n"
            f"Domain: {domain}\n"
            f"IP Address: {ip_address}\n"
            f"Response Time: {response_time:.2f} ms\n"
            f"TTL: {actual_ttl} seconds"
        )

    except Exception as exc:
        return f"DNS resolution failed: {exc}"


# --------------------------------------------------
# ADAPTIVE CACHE SIZE
# --------------------------------------------------

def adapt_cache_size():
    global MAX_CACHE_SIZE
    global adaptive_queries
    global adaptive_hits

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

    if MAX_CACHE_SIZE == old_size:
        return None

    print(
        "Adaptive cache size changed:",
        old_size,
        "->",
        MAX_CACHE_SIZE,
        "| Hit ratio:",
        round(hit_ratio, 2),
        "%"
    )

    # Remove entries if cache exceeds the new capacity
    remove_expired_entries()

    while len(cache) > MAX_CACHE_SIZE:
        domain_to_remove = (
            select_cache_entry_for_replacement()
        )

        if domain_to_remove is None:
            break

        print(
            "Adaptive resizing: evicting",
            domain_to_remove
        )
        del cache[domain_to_remove]

    return (
        f"Cache size changed from {old_size} "
        f"to {MAX_CACHE_SIZE}"
    )


# --------------------------------------------------
# STATISTICS
# --------------------------------------------------

def get_statistics():
    lines = [
        "",
        "===================================",
        "       DNS RESOLVER STATISTICS",
        "===================================",
        f"Total Queries: {total_queries}",
        f"Cache Hits: {cache_hits}",
        f"Cache Misses: {cache_misses}",
        f"DNS Queries Sent: {dns_queries}"
    ]

    if total_queries > 0:
        hit_ratio = (
            cache_hits / total_queries
        ) * 100

        lines.append(
            f"Cache Hit Ratio: {hit_ratio:.2f}%"
        )

    if dns_queries > 0:
        average_time = (
            total_dns_response_time / dns_queries
        )

        lines.append(
            f"Average DNS Response Time: {average_time:.2f} ms"
        )

    remove_expired_entries()

    lines.extend([
        f"Cache Size: {len(cache)}",
        f"Maximum Cache Size: {MAX_CACHE_SIZE}",
        "==================================="
    ])

    return "\n".join(lines)


# --------------------------------------------------
# CACHE CONTENTS
# --------------------------------------------------

def get_cache_contents():
    remove_expired_entries()
    current_time = time.time()

    lines = [
        "",
        "===================================",
        "          CACHE CONTENTS",
        "==================================="
    ]

    if not cache:
        lines.append("Cache is empty")

    else:
        for domain, entry in cache.items():
            remaining_ttl = max(
                0.0,
                entry["expiry"] - current_time
            )

            last_access = time.strftime(
                "%H:%M:%S",
                time.localtime(entry["last_access"])
            )

            lines.extend([
                f"Domain: {domain}",
                f"IP Address: {entry['ip']}",
                f"Frequency: {entry['frequency']}",
                f"TTL Remaining: {remaining_ttl:.2f} seconds",
                f"Last Access: {last_access}",
                "-----------------------------------"
            ])

    lines.append("===================================")

    return "\n".join(lines)


# --------------------------------------------------
# RESET STATISTICS
# --------------------------------------------------

def reset_statistics():
    global total_queries
    global cache_hits
    global cache_misses
    global dns_queries
    global total_dns_response_time
    global adaptive_queries
    global adaptive_hits

    total_queries = 0
    cache_hits = 0
    cache_misses = 0
    dns_queries = 0
    total_dns_response_time = 0.0
    adaptive_queries = 0
    adaptive_hits = 0


# --------------------------------------------------
# MAIN SERVER LOOP
# --------------------------------------------------

def main():
    global MAX_CACHE_SIZE

    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    try:
        server_socket.bind((HOST, PORT))

    except OSError as exc:
        server_socket.close()

        print(
            f"Could not bind to {HOST}:{PORT}: {exc}"
        )
        print(
            "Check whether another DNS server is already using port",
            PORT
        )
        return

    print("DNS Resolver Server started")
    print("Listening on", HOST, "port", PORT)
    print("Maximum Cache Size:", MAX_CACHE_SIZE)

    try:
        while True:
            data, client_address = server_socket.recvfrom(1024)

            request = data.decode(
                errors="replace"
            ).strip()

            command = request.lower()

            print("\nRequest received:", request)

            if command == "stats":
                response = get_statistics()

            elif command == "cache":
                response = get_cache_contents()

            elif command == "clear":
                cache.clear()
                response = "Cache cleared successfully"

            elif command.startswith("setsize "):
                try:
                    parts = request.split()

                    if len(parts) != 2:
                        raise ValueError(
                            "use: setsize <number>"
                        )

                    new_size = int(parts[1])

                    if new_size <= 0:
                        raise ValueError(
                            "cache size must be positive"
                        )

                    old_size = MAX_CACHE_SIZE

                    MAX_CACHE_SIZE = max(
                        MIN_CACHE_SIZE,
                        min(
                            new_size,
                            MAX_ALLOWED_CACHE_SIZE
                        )
                    )

                    while len(cache) > MAX_CACHE_SIZE:
                        domain_to_remove = (
                            select_cache_entry_for_replacement()
                        )

                        if domain_to_remove is None:
                            break

                        print(
                            "Manual resizing: evicting",
                            domain_to_remove
                        )
                        del cache[domain_to_remove]

                    response = (
                        f"Maximum cache size set to {MAX_CACHE_SIZE} "
                        f"(previously {old_size})"
                    )

                except (ValueError, IndexError) as exc:
                    response = f"Invalid cache size: {exc}"

            elif command == "resetstats":
                reset_statistics()
                response = "Statistics reset successfully"

            else:
                response = resolve_domain(request)

                # Evaluate after each DNS request
                adapt_cache_size()

            server_socket.sendto(
                response.encode(),
                client_address
            )

    except KeyboardInterrupt:
        print("\nDNS Resolver Server stopped")

    finally:
        server_socket.close()


if __name__ == "__main__":
    main()