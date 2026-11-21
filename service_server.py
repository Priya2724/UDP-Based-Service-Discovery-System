import argparse
import socket
import threading
import time
import uuid
from protocol import *

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", required=True)
    p.add_argument("--port", type=int, default=5001)
    p.add_argument("--discovery", default="10.0.0.2")
    p.add_argument("--discovery-port", type=int, default=5000)
    p.add_argument("--service", default="Calculator")
    p.add_argument("--heartbeat", type=float, default=2.0)
    args = p.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    ds = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ds.settimeout(2)

    def announce(kind):
        msg = {"type": kind, "service": args.service,
               "ip": args.host, "port": args.port}
        try:
            ds.sendto(encode(msg), (args.discovery, args.discovery_port))
            ds.recvfrom(4096)
        except socket.timeout:
            print("[WARN] Discovery server did not reply", flush=True)
        except OSError as e:
            print("[WARN]", e, flush=True)

    announce(REGISTER)
    def beat():
        while True:
            time.sleep(args.heartbeat)
            announce(HEARTBEAT)
    threading.Thread(target=beat, daemon=True).start()
    print(f"[SERVICE] {args.service} listening at {args.host}:{args.port}", flush=True)

    while True:
        data, addr = sock.recvfrom(65535)
        try:
            msg = decode(data)
            if msg.get("type") == SERVICE_REQUEST:
                reply = {"type": SERVICE_RESPONSE,
                         "service": args.service,
                         "server": args.host,
                         "result": "Calculator service is available",
                         "request_id": msg.get("request_id")}
            else:
                reply = {"type": ERROR, "message": "Unknown service request"}
            sock.sendto(encode(reply), addr)
        except Exception as exc:
            print("[ERROR]", repr(exc), flush=True)

if __name__ == "__main__":
    main()
