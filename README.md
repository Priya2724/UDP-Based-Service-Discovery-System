# UDP-Based Service Discovery System using Mininet and SDN 

## Overview
The basic service-discovery setup is used to a five-host Mininet topology. It uses a UDP discovery server, two Calculator service-server instances, Round Robin selection, heartbeat-based availability tracking, and an OS-Ken controller using OpenFlow 1.3.

> This is the implementation package prepared from the source archive used during the working demo. The controller base class is set to `app_manager.OSKenApp`, matching the OS-Ken version used in the demonstrated environment.

## Topology and addressing

| Host | Address | Role |
|---|---|---|
| h1 | 10.0.0.1/24 | Client 1 |
| h2 | 10.0.0.2/24 | Discovery server, UDP 5000 |
| h3 | 10.0.0.3/24 | Calculator service server 1, UDP 5001 |
| h4 | 10.0.0.4/24 | Client 2 |
| h5 | 10.0.0.5/24 | Calculator service server 2, UDP 5001 |

All five hosts connect to OVS switch `s1`. The switch uses OpenFlow 1.3 and connects to the OS-Ken controller.

## Files

- `topology.py` — creates the five-host Mininet topology.
- `controller.py` — OS-Ken OpenFlow 1.3 learning-switch controller.
- `protocol.py` — JSON message constants and encode/decode helpers.
- `service_registry.py` — stores service instances, expires stale registrations, and selects active instances using Round Robin.
- `discovery_server_integrated.py` — handles registration, heartbeat, and discovery UDP messages.
- `service_server.py` — runs a service-server instance and periodically sends registration/heartbeat messages.
- `client.py` — discovers a service and sends a request to the selected server.
- `performance_test.py` — measures discovery latency, throughput, and success rate.

## Requirements

- Ubuntu Linux
- Python 3
- Mininet
- Open vSwitch
- OS-Ken installed in the Python environment used for the controller
- Wireshark (optional, for packet capture)

The application files use Python standard-library modules. Mininet, OVS and OS-Ken are system/environment dependencies rather than packages installed by this project script.

## Run the project

Open separate Ubuntu terminals.

### 1. Start the OS-Ken controller

```bash
cd UDP_Service-Discovery
python3 -m venv ~/osken-env
source ~/osken-env/bin/activate
pip install os-ken
python -c "from os_ken.base import app_manager; app_manager.AppManager.run_apps(['controller'])"
```

Leave this terminal running.

### 2. Start Mininet

```bash
cd UDP_Service_Discovery
sudo mn -c
sudo python3 topology.py
```

Wait for the `mininet>` prompt.

### 3. Check topology and connectivity

At `mininet>`:

```text
net
pingall
```

The demonstrated run reported 20/20 packets received and 0% loss.

### 4. Start the discovery server

At `mininet>`:

```text
h2 python3 -u discovery_server_integrated.py --host 10.0.0.2 --port 5000 &
```


### 5. Start both service servers

```text
h3 python3 -u service_server.py --host 10.0.0.3 --port 5001 --discovery 10.0.0.2 --discovery-port 5000 --service Calculator --heartbeat 2 &
h5 python3 -u service_server.py --host 10.0.0.5 --port 5001 --discovery 10.0.0.2 --discovery-port 5000 --service Calculator --heartbeat 2 &
```

### 6. Test discovery and service request

Run repeatedly from `mininet>`:

```text
h1 python3 -u client.py Calculator --server 10.0.0.2 --port 5000
```

With both servers active, the registry should alternate selection between `10.0.0.3` and `10.0.0.5`.

### 7. Run performance test

```text
h1 python3 -u performance_test.py --server 10.0.0.2 --port 5000 --count 20
```

Performance values depend on the environment and run. A previously recorded run produced 20 successful requests, 0 failures, 1.575 ms average discovery latency, 601.416 successful requests/second, and 100% success rate.

### 8. Verify OpenFlow

At `mininet>`:

```text
sh ovs-vsctl show
sh ovs-vsctl get bridge s1 protocols
sh ovs-ofctl -O OpenFlow13 dump-flows s1
```

Expected protocol output is `[OpenFlow13]`. The flow dump should show forwarding entries and packet/byte counters after traffic has passed.

## Failure and recovery test

At `mininet>`, find the current process ID (PID) for h3:

```text
h3 ss -lunp | grep 5001
```

Stop h3 using the actual PID shown:

```text
h3 kill <PID>
```

Wait about 10 seconds for the configured 8-second registry timeout, then run the client again. It should select h5.

Repeat for h5. If both service servers are stopped and their registrations expire, the client should receive `NOT_FOUND`.

Restart the two service-server commands above to demonstrate recovery. Use the current PID each time; do not reuse an old PID.

## Wireshark

Start a capture on `s1-eth1` (or another relevant Mininet interface) and generate new client requests while capturing.

Useful display filters:

```text
udp.port == 5000
udp.port == 5001
tcp.port == 6653
```

- UDP 5000: discovery, registration and heartbeat messages.
- UDP 5001: service requests and responses.
- TCP 6653: OpenFlow controller-switch connection.

Capturing on `s1-eth1` shows traffic on that host-facing switch port; it does not automatically show every host's traffic.

## Design notes and scope

- Round Robin selection is implemented in `service_registry.py`, not in the SDN controller.
- The controller handles OpenFlow switch events and MAC-learning-based forwarding.
- The application uses UDP. OpenFlow control traffic uses a separate TCP connection.
- The provided Calculator endpoint is a demonstration service that returns an availability/status response; this package does not implement arithmetic operations.
- h4 is included in the topology as a second client. The primary recorded client and performance commands use h1.
- The performance figures above are prior observed results, not guaranteed values for every run.
