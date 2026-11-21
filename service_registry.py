import threading
import time

class ServiceRegistry:
    def __init__(self, timeout=8.0):
        self.timeout = timeout
        self.services = {}
        self.next_index = {}
        self.lock = threading.RLock()

    def register(self, name, ip, port):
        if not name or not ip or not isinstance(port, int) or not 1 <= port <= 65535:
            raise ValueError("Invalid service registration")
        with self.lock:
            instances = self.services.setdefault(name, {})
            instances[(ip, port)] = {
                "name": name, "ip": ip, "port": port,
                "status": "ACTIVE", "last_seen": time.monotonic()
            }
        print(f"[REGISTER] {name} {ip}:{port}", flush=True)
        return True

    def heartbeat(self, name, ip, port):
        with self.lock:
            entry = self.services.get(name, {}).get((ip, port))
            if entry is None:
                return False
            entry["last_seen"] = time.monotonic()
            entry["status"] = "ACTIVE"
            return True

    def _expire(self):
        now = time.monotonic()
        for instances in self.services.values():
            for entry in instances.values():
                if now - entry["last_seen"] > self.timeout:
                    entry["status"] = "INACTIVE"

    def discover(self, name):
        with self.lock:
            self._expire()
            active = sorted(
                [dict(x) for x in self.services.get(name, {}).values()
                 if x["status"] == "ACTIVE"],
                key=lambda x: (x["ip"], x["port"])
            )
            if not active:
                print(f"[NOT_FOUND] {name}", flush=True)
                return None
            idx = self.next_index.get(name, 0) % len(active)
            chosen = active[idx]
            self.next_index[name] = (idx + 1) % len(active)
            print(f"[ROUND ROBIN] {name} -> {chosen['ip']}:{chosen['port']}", flush=True)
            return chosen

    def list_services(self):
        with self.lock:
            self._expire()
            return {name: [dict(x) for x in items.values()]
                    for name, items in self.services.items()}
