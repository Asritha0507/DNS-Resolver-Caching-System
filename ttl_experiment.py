import socket
import time

SERVER = "127.0.0.1"
PORT = 5000

domain = "google.com"

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


print("\nTTL EXPIRATION EXPERIMENT")
print("=" * 50)

# Clear cache
send_request("clear")

# First request
print("\n1. First Request")

response = send_request(domain)

print(response)

# Extract TTL
ttl = None

for line in response.split("\n"):

    if line.startswith("TTL:"):

        ttl = int(
            line.split(":")[1].strip().split()[0]
        )

if ttl is None:

    print("\nTTL could not be detected.")
    client_socket.close()
    exit()

print("\nTTL received:", ttl, "seconds")

# Wait until TTL expires
print("\nWaiting for TTL to expire...")

time.sleep(ttl + 1)

# Request after expiration
print("\n2. Request After TTL Expiration")

response = send_request(domain)

print(response)

client_socket.close()

print("\n" + "=" * 50)
print("TTL experiment completed")