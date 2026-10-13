import time

MAX_CACHE_SIZE = 3
current_time = time.time()

cache = {
    "longttl.com": {
        "frequency": 5,
        "last_access": current_time - 10,
        "expiry": current_time + 300
    },
    "mediumttl.com": {
        "frequency": 5,
        "last_access": current_time - 10,
        "expiry": current_time + 120
    },
    "shortttl.com": {
        "frequency": 5,
        "last_access": current_time - 10,
        "expiry": current_time + 10
    }
}


def select_cache_entry_for_replacement():
    current_time = time.time()

    for domain, entry in list(cache.items()):
        if current_time >= entry["expiry"]:
            del cache[domain]

    if len(cache) < MAX_CACHE_SIZE:
        return None

    scores = {}

    for domain, entry in cache.items():
        frequency = entry["frequency"]
        popularity_score = frequency / (frequency + 1)

        age = current_time - entry["last_access"]
        recency_score = 1 / (1 + age)

        remaining_ttl = max(
            0, entry["expiry"] - current_time
        )
        ttl_score = remaining_ttl / (remaining_ttl + 60)

        score = (
            0.5 * popularity_score
            + 0.3 * recency_score
            + 0.2 * ttl_score
        )

        scores[domain] = score

    print("Replacement scores:")
    for domain, score in scores.items():
        print("{}: {:.4f}".format(domain, score))

    return min(scores, key=scores.get) if scores else None


print("TTL-AWARE REPLACEMENT TEST")
print("=" * 35)

victim = select_cache_entry_for_replacement()
print("Selected entry:", victim)

if victim == "shortttl.com":
    print("PASS: Entry with shortest remaining TTL selected.")
else:
    print("FAIL: Unexpected entry selected.")
