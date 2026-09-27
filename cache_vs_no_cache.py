import socket
import time

SERVER = "127.0.0.1"
PORT = 5000

domains = [
    "google.com",
    "youtube.com",
    "github.com"
]

TOTAL_REQUESTS = 15


def send_request(request):

    client_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    start_time = time.time()

    client_socket.sendto(
        request.encode(),
        (SERVER, PORT)
    )

    data, server_address = client_socket.recvfrom(2048)

    end_time = time.time()

    client_socket.close()

    response_time = (end_time - start_time) * 1000

    return data.decode(), response_time


def run_experiment(cache_size):

    send_request("setsize " + str(cache_size))

    hits = 0
    misses = 0
    total_time = 0

    for i in range(TOTAL_REQUESTS):

        # Alternate between the three domains
        domain = domains[i % len(domains)]

        response, response_time = send_request(
            domain
        )

        total_time += response_time

        if "CACHE HIT" in response:

            hits += 1

        else:

            misses += 1

    total_requests = hits + misses

    hit_ratio = (
        hits / total_requests
    ) * 100

    average_time = (
        total_time / total_requests
    )

    return (
        total_requests,
        hits,
        misses,
        hit_ratio,
        average_time
    )


print("\nCACHE VS NO-CACHE EXPERIMENT")
print("=" * 60)


# ------------------------------------------------
# CASE 1: SMALL CACHE
# ------------------------------------------------

print("\nCASE 1: CACHE SIZE = 1")
print("-" * 60)

send_request("clear")

results_small = run_experiment(1)

print("Total Requests:", results_small[0])
print("Cache Hits:", results_small[1])
print("Cache Misses:", results_small[2])
print("Cache Hit Ratio: {:.2f}%".format(
    results_small[3]
))
print("Average Response Time: {:.2f} ms".format(
    results_small[4]
))


# ------------------------------------------------
# CASE 2: EFFECTIVE CACHE
# ------------------------------------------------

print("\nCASE 2: CACHE SIZE = 3")
print("-" * 60)

send_request("clear")

results_large = run_experiment(3)

print("Total Requests:", results_large[0])
print("Cache Hits:", results_large[1])
print("Cache Misses:", results_large[2])
print("Cache Hit Ratio: {:.2f}%".format(
    results_large[3]
))
print("Average Response Time: {:.2f} ms".format(
    results_large[4]
))


# ------------------------------------------------
# COMPARISON
# ------------------------------------------------

print("\n" + "=" * 60)
print("COMPARISON")
print("=" * 60)

time_small = results_small[4]
time_large = results_large[4]

if time_small > 0:

    improvement = (
        (time_small - time_large)
        / time_small
    ) * 100

    print(
        "Average Response Time Improvement: {:.2f}%".format(
            improvement
        )
    )

dns_queries_avoided = (
    results_small[2] - results_large[2]
)

print(
    "DNS Queries Avoided:",
    dns_queries_avoided
)

print("=" * 60)

print("\nExperiment completed")