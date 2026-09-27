import socket
import time

SERVER = "127.0.0.1"
PORT = 5000

domains = [
    "google.com",
    "youtube.com",
    "github.com"
]

number_of_requests = 20

client_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)


def send_request(request):

    client_socket.sendto(
        request.encode(),
        (SERVER, PORT)
    )

    data, server_address = client_socket.recvfrom(2048)

    return data.decode()


# Clear cache
send_request("clear")

total_time = 0
cache_hits = 0
cache_misses = 0

print("\nDNS CACHE PERFORMANCE EXPERIMENT")
print("=" * 50)

for i in range(number_of_requests):

    # Select domain
    domain = domains[i % len(domains)]

    start_time = time.time()

    response = send_request(domain)

    end_time = time.time()

    response_time = (end_time - start_time) * 1000

    total_time += response_time

    # Check cache status
    if response.startswith("CACHE HIT"):
        cache_hits += 1
        status = "HIT"

    else:
        cache_misses += 1
        status = "MISS"

    print(
        "Request {:2d} | {:15s} | {:4s} | {:.2f} ms".format(
            i + 1,
            domain,
            status,
            response_time
        )
    )


average_time = total_time / number_of_requests

hit_ratio = (
    cache_hits / number_of_requests
) * 100


print("\n" + "=" * 50)
print("EXPERIMENT RESULTS")
print("=" * 50)

print("Total Requests:", number_of_requests)
print("Cache Hits:", cache_hits)
print("Cache Misses:", cache_misses)
print("Cache Hit Ratio: {:.2f}%".format(hit_ratio))
print("Average Response Time: {:.2f} ms".format(
    average_time
))

print("=" * 50)

client_socket.close()