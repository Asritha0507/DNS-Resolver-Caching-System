import socket
import time

SERVER = "127.0.0.1"
PORT = 5000

domain_sets = {

    3: [
        "google.com",
        "youtube.com",
        "github.com"
    ],

    5: [
        "google.com",
        "youtube.com",
        "github.com",
        "amazon.com",
        "microsoft.com"
    ],

    10: [
        "google.com",
        "youtube.com",
        "github.com",
        "amazon.com",
        "microsoft.com",
        "facebook.com",
        "wikipedia.org",
        "linkedin.com",
        "reddit.com",
        "apple.com"
    ]
}

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


print("\nDOMAIN VARIATION EXPERIMENT")
print("=" * 55)


for number_of_domains, domains in domain_sets.items():

    # Clear cache
    send_request("clear")

    cache_hits = 0
    cache_misses = 0
    total_time = 0

    print("\nTesting", number_of_domains, "unique domains")
    print("-" * 55)

    for i in range(number_of_requests):

        domain = domains[i % number_of_domains]

        start_time = time.time()

        response = send_request(domain)

        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        total_time += response_time

        if response.startswith("CACHE HIT"):
            cache_hits += 1
        else:
            cache_misses += 1

    hit_ratio = (
        cache_hits / number_of_requests
    ) * 100

    average_time = (
        total_time / number_of_requests
    )

    print("Total Requests:", number_of_requests)
    print("Unique Domains:", number_of_domains)
    print("Cache Hits:", cache_hits)
    print("Cache Misses:", cache_misses)
    print("Cache Hit Ratio: {:.2f}%".format(hit_ratio))
    print(
        "Average Response Time: {:.2f} ms"
        .format(average_time)
    )


client_socket.close()

print("\n" + "=" * 55)
print("Experiment completed")