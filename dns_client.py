import socket

SERVER = "127.0.0.1"
PORT = 5000

while True:

    domain = input(
        "\nEnter domain name "
        "(or 'stats' or 'exit'): "
    )

    if domain.lower() == "exit":
        break

    client_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    client_socket.sendto(
        domain.encode(),
        (SERVER, PORT)
    )

    data, server_address = client_socket.recvfrom(2048)

    print("\nResponse from server:")
    print(data.decode())

    client_socket.close()