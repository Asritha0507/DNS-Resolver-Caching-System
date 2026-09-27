import socket
import time

SERVER = "127.0.0.1"
PORT = 5000

domains = [
    "google.com",
    "youtube.com",
    "github.com",
    "microsoft.com",
    "amazon.com",
    "wikipedia.org",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "stackoverflow.com"
]


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


print("\nCACHE SIZE EXPERIMENT")
print("=" * 60)

cache_sizes = [3, 5, 10]

total_requests = 20

for cache_size in cache_sizes:

    print("\nTesting Cache Size:", cache_size)
    print("-" * 60)

    # Set cache size
    response, time_taken = send_request(
        "setsize " + str(cache_size)
    )

    print(response)

    hits = 0
    misses = 0
    total_time = 0

    # Generate 20 requests
    for i in range(total_requests):

        domain = domains[i % len(domains)]

        response, response_time = send_request(
            domain
        )

        total_time += response_time

        if "CACHE HIT" in response:
            hits += 1
        else:
            misses += 1

        print(
            "Request {:2d} | {:20s} | {:4s} | {:.2f} ms".format(
                i + 1,
                domain,
                "HIT" if "CACHE HIT" in response else "MISS",
                response_time
            )
        )

    hit_ratio = (hits / total_requests) * 100

    average_time = total_time / total_requests

    print("\nResults:")
    print("Cache Size:", cache_size)
    print("Total Requests:", total_requests)
    print("Cache Hits:", hits)
    print("Cache Misses:", misses)
    print("Cache Hit Ratio: {:.2f}%".format(hit_ratio))
    print("Average Response Time: {:.2f} ms".format(
        average_time
    ))

print("\n" + "=" * 60)
print("Cache size experiment completed")