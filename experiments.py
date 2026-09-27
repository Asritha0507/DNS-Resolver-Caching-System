import socket
import time

SERVER = "127.0.0.1"
PORT = 5000

domains = [
    "google.com",
    "youtube.com",
    "github.com"
]

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


print("\nDNS CACHE PERFORMANCE EXPERIMENT")
print("=" * 50)

for domain in domains:

    # Clear cache before testing this domain
    response = send_request("clear")

    print("\nDomain:", domain)
    print("Cache:", response)

    # First request - Cache Miss
    start_time = time.time()

    response = send_request(domain)

    end_time = time.time()

    first_time = (end_time - start_time) * 1000

    print("First Request Time: {:.2f} ms".format(first_time))
    print("First Request Status:", response.split("\n")[0])

    # Second request - Cache Hit
    start_time = time.time()

    response = send_request(domain)

    end_time = time.time()

    second_time = (end_time - start_time) * 1000

    print("Second Request Time: {:.2f} ms".format(second_time))
    print("Second Request Status:", response.split("\n")[0])

    # Calculate improvement
    if first_time > 0:

        improvement = (
            (first_time - second_time)
            / first_time
        ) * 100

        print(
            "Response Time Improvement: {:.2f}%"
            .format(improvement)
        )

client_socket.close()

print("\n" + "=" * 50)
print("Experiment completed")