from flask import Flask, render_template, request, jsonify
import socket
import time

app = Flask(__name__)

DNS_SERVER = "127.0.0.1"
DNS_PORT = 5000


def send_to_dns_server(message):

    client_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    client_socket.settimeout(5)

    try:

        start_time = time.time()

        client_socket.sendto(
            message.encode(),
            (DNS_SERVER, DNS_PORT)
        )

        data, server_address = client_socket.recvfrom(4096)

        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        return data.decode(), response_time

    except socket.timeout:

        return "ERROR: DNS server did not respond", 0

    except Exception as e:

        return "ERROR: " + str(e), 0

    finally:

        client_socket.close()


def parse_response(response):

    lines = response.split("\n")

    result = {
        "status": "",
        "domain": "",
        "ip": "",
        "response_time": "",
        "ttl": "",
        "ttl_remaining": ""
    }

    if lines:
        result["status"] = lines[0]

    for line in lines:

        if line.startswith("Domain:"):
            result["domain"] = line.replace(
                "Domain:", ""
            ).strip()

        elif line.startswith("IP Address:"):
            result["ip"] = line.replace(
                "IP Address:", ""
            ).strip()

        elif line.startswith("Response Time:"):
            result["response_time"] = line.replace(
                "Response Time:", ""
            ).strip()

        elif line.startswith("TTL:"):
            result["ttl"] = line.replace(
                "TTL:", ""
            ).strip()

        elif line.startswith("TTL Remaining:"):
            result["ttl_remaining"] = line.replace(
                "TTL Remaining:", ""
            ).strip()

    return result


@app.route("/")
def home():

    return render_template("index.html")


@app.route("/resolve", methods=["POST"])
def resolve():

    data = request.get_json()

    domain = data.get(
        "domain",
        ""
    ).strip()

    if not domain:

        return jsonify({
            "error": "Please enter a domain name"
        })


    response, response_time = send_to_dns_server(
        domain
    )


    if response.startswith("ERROR"):

        return jsonify({
            "error": response
        })


    result = parse_response(response)


    # Actual end-to-end response time
    # measured between Flask and DNS resolver
    result["response_time"] = "{:.2f} ms".format(
        response_time
    )


    return jsonify(result)


@app.route("/stats")
def stats():

    response, response_time = send_to_dns_server(
        "stats"
    )

    return jsonify({
        "data": response
    })


@app.route("/clear", methods=["POST"])
def clear():

    response, response_time = send_to_dns_server(
        "clear"
    )

    return jsonify({
        "message": response
    })


@app.route("/setsize", methods=["POST"])
def setsize():

    data = request.get_json()

    size = data.get("size")


    try:

        size = int(size)

        if size <= 0:
            raise ValueError

    except:

        return jsonify({
            "error": "Invalid cache size"
        })


    response, response_time = send_to_dns_server(
        "setsize " + str(size)
    )


    return jsonify({
        "message": response
    })


if __name__ == "__main__":

    print("Flask web application started")

    print(
        "Open http://127.0.0.1:8000 in your browser"
    )

    app.run(
        host="127.0.0.1",
        port=8000,
        debug=True
    )