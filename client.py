import argparse
import socket
import time
import uuid
from protocol import *

def discover(server, port, service, timeout):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    rid = str(uuid.uuid4())
    start = time.perf_counter()
    sock.sendto(encode({"type": DISCOVER, "service": service,
                        "request_id": rid}), (server, port))
    data, addr = sock.recvfrom(4096)
    elapsed = (time.perf_counter() - start) * 1000
    reply = decode(data)
    if reply.get("request_id") != rid:
        raise RuntimeError("Mismatched request ID")
    if reply.get("type") == NOT_FOUND:
        print("NOT_FOUND: service is currently unavailable")
        return None
    if reply.get("type") != FOUND:
        raise RuntimeError("Discovery server returned an error: " + str(reply))
    print(f"FOUND {service} at {reply['ip']}:{reply['port']} ({elapsed:.3f} ms)")
    sock.close()
    return reply

def main():
    p = argparse.ArgumentParser()
    p.add_argument("service", nargs="?", default="Calculator")
    p.add_argument("--server", default="10.0.0.2")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--timeout", type=float, default=3)
    args = p.parse_args()
    try:
        result = discover(args.server, args.port, args.service, args.timeout)
        if not result:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        rid = str(uuid.uuid4())
        sock.sendto(encode({"type": SERVICE_REQUEST, "request_id": rid}),
                    (result["ip"], result["port"]))
        data, _ = sock.recvfrom(4096)
        response = decode(data)
        print("SERVICE RESPONSE:", response)
    except Exception as exc:
        print("Client error:", exc)

if __name__ == "__main__":
    main()
