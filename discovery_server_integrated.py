import argparse
import socket
from protocol import *

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="10.0.0.2")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--timeout", type=float, default=8.0)
    args = p.parse_args()

    from service_registry import ServiceRegistry
    registry = ServiceRegistry(args.timeout)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    print(f"[DISCOVERY] Listening on {args.host}:{args.port}", flush=True)

    while True:
        data, addr = sock.recvfrom(65535)
        try:
            msg = decode(data)
            kind = msg.get("type")
            name = msg.get("service", "Calculator")
            if kind == REGISTER:
                ip = msg.get("ip", addr[0])
                port = int(msg["port"])
                registry.register(name, ip, port)
                reply = {"type": OK}
            elif kind == HEARTBEAT:
                ip = msg.get("ip", addr[0])
                port = int(msg["port"])
                if registry.heartbeat(name, ip, port):
                    reply = {"type": OK}
                else:
                    registry.register(name, ip, port)
                    reply = {"type": OK}
            elif kind == DISCOVER:
                found = registry.discover(name)
                reply = ({"type": FOUND, "ip": found["ip"], "port": found["port"]}
                         if found else {"type": NOT_FOUND})
            else:
                reply = {"type": ERROR, "message": "Unknown request"}
            if "request_id" in msg:
                reply["request_id"] = msg["request_id"]
        except Exception as exc:
            print("[ERROR]", repr(exc), flush=True)
            reply = {"type": ERROR, "message": str(exc)}
        sock.sendto(encode(reply), addr)

if __name__ == "__main__":
    main()
