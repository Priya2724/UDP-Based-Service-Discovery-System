import argparse
import socket
import time
import uuid
from protocol import *

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--server", default="10.0.0.2")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--service", default="Calculator")
    p.add_argument("--count", type=int, default=20)
    args = p.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(3)
    latencies = []
    success = 0
    started = time.perf_counter()
    for _ in range(args.count):
        rid = str(uuid.uuid4())
        t0 = time.perf_counter()
        try:
            sock.sendto(encode({"type": DISCOVER, "service": args.service,
                                "request_id": rid}), (args.server, args.port))
            data, _ = sock.recvfrom(4096)
            msg = decode(data)
            if msg.get("request_id") == rid and msg.get("type") == FOUND:
                success += 1
                latencies.append((time.perf_counter() - t0) * 1000)
        except (socket.timeout, OSError):
            pass
    duration = time.perf_counter() - started
    print("Requests:", args.count)
    print("Successful:", success)
    print("Failed:", args.count - success)
    print("Average discovery latency (ms):",
          round(sum(latencies) / len(latencies), 3) if latencies else "N/A")
    print("Throughput (successful requests/sec):",
          round(success / duration, 3) if duration else 0)
    print("Success rate (%):", round(success * 100 / args.count, 2))
    sock.close()

if __name__ == "__main__":
    main()
