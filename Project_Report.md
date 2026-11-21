# Project Report
## UDP-Based Service Discovery System using Mininet and SDN
### Multiple Service Servers, Round Robin Selection and Failure Handling

**Course:** [Computer Networks]

## Abstract

This project implements a UDP-based service-discovery system in a software-defined networking (SDN) environment using Mininet, Open vSwitch (OVS), and OS-Ken. We used five-host topology containing two client hosts, one discovery server, and two service-server instances. The discovery server maintains service registrations and uses Round Robin selection to distribute discovery responses among active instances. Service servers periodically send heartbeat messages so that stale registrations can be marked inactive. The system was tested for normal discovery, server failure, fallback to the remaining server, the no-server-available case, and recovery after servers restart. Performance was measured using a 20-request test, and packet exchanges were inspected with Wireshark.

## 1. Introduction

Service discovery allows a client to locate a network service without needing to know in advance which server instance will handle the request. In this project, a client sends a discovery request to a central discovery server. The discovery server consults its service registry and returns the address and port of an available service instance. The client then sends its service request directly to that instance.

The project uses UDP for application-level registration, heartbeat, discovery, and service messages. Mininet emulates the network, OVS provides switching, and an OS-Ken controller manages switch forwarding using OpenFlow 1.3.

## 2. Objectives

1. Build and test a UDP service-discovery application.
2. Emulate a five-host network using Mininet.
3. Register multiple instances of the same service.
4. Distribute service selections using Round Robin.
5. Detect inactive service instances using heartbeat timeouts.
6. Test failure handling and recovery.
7. Measure discovery latency, throughput, and success rate.
8. Inspect network packets using Wireshark.
9. Verify the OpenFlow 1.3 switch-controller configuration.

## 3. System Architecture

### 3.1 Host configuration

| Host | IP address | Function |
|---|---|---|
| h1 | 10.0.0.1 | Client 1 |
| h2 | 10.0.0.2 | Discovery server and service registry, UDP 5000 |
| h3 | 10.0.0.3 | Service server 1, UDP 5001 |
| h4 | 10.0.0.4 | Client 2 |
| h5 | 10.0.0.5 | Service server 2, UDP 5001 |

All hosts are connected to a single OVS switch named `s1`. The switch is configured for OpenFlow 1.3 and connects to the OS-Ken controller at `127.0.0.1:6653`.

### 3.2 Architecture components

- **Client:** Requests discovery of the Calculator service and sends a service request to the returned server.
- **Discovery server:** Receives registration, heartbeat, and discovery messages on UDP port 5000.
- **Service registry:** Stores service instances, tracks their last heartbeat time, marks stale instances inactive, and selects active instances using Round Robin.
- **Service servers:** Run on h3 and h5, listen on UDP port 5001, register with the discovery server, and send periodic heartbeats.
- **OVS switch:** Connects the Mininet hosts.
- **OS-Ken controller:** Handles OpenFlow 1.3 switch events and installs forwarding flows using MAC learning.

## 4. Working Methodology

### 4.1 Service registration

When a service-server process starts, it sends a `REGISTER` message containing its service name, IP address, and port to the discovery server. The registry stores each instance separately, allowing h3 and h5 to register the same service name.

### 4.2 Heartbeat monitoring

Each service-server process sends a `HEARTBEAT` message periodically. The demonstrated startup command configures a heartbeat interval of 2 seconds. The registry uses an 8-second timeout by default. If the time since the last heartbeat exceeds this timeout, the corresponding instance is marked `INACTIVE`.

### 4.3 Service discovery and Round Robin

A client sends a `DISCOVER` request to h2. The registry filters the service instances to include only active entries, sorts them by IP address and port, and chooses an instance using a per-service next-index counter. The counter advances cyclically across the active list. The discovery server responds with `FOUND` and the selected server address and port, or `NOT_FOUND` if no active instance exists.

### 4.4 Service request

After receiving a `FOUND` response, the client sends a `SERVICE_REQUEST` message directly to the selected service server. The demonstration server responds with a `SERVICE_RESPONSE` status message. The current Calculator endpoint is a service-discovery demonstration endpoint; it returns an availability response rather than performing arithmetic calculations.

### 4.5 SDN forwarding

The OS-Ken controller communicates with OVS using OpenFlow 1.3. It learns source MAC addresses from Packet-In events and installs forwarding entries for known destination MAC addresses. This switching function is separate from the application-level Round Robin selection.

## 5. Implementation Files

| File | Responsibility |
|---|---|
| `topology.py` | Creates the five-host Mininet topology and connects it to the remote controller. |
| `controller.py` | Implements the OS-Ken OpenFlow 1.3 learning-switch application. |
| `protocol.py` | Defines message types and JSON encoding/decoding functions. |
| `service_registry.py` | Maintains service instances, heartbeat timestamps, timeout status, and Round Robin selection. |
| `discovery_server_integrated.py` | Handles registration, heartbeat, and discovery UDP messages. |
| `service_server.py` | Runs each service-server instance and sends registration/heartbeat messages. |
| `client.py` | Discovers a service and sends a request to the selected instance. |
| `performance_test.py` | Sends repeated discovery requests and calculates performance metrics. |

## 6. Testing and Results

### 6.1 Network connectivity

The Mininet topology was started and `pingall` was executed. The recorded test result was 20 packets received out of 20, with 0% packet loss.

### 6.2 Round Robin selection

Both service servers were started and the client discovery command was run repeatedly. The selected service-server address alternated between `10.0.0.3` and `10.0.0.5`, demonstrating cyclic selection while both instances were active.

### 6.3 Failure detection and recovery

| Test case | Expected behaviour | Observed result |
|---|---|---|
| Stop h3 while h5 is active | h5 should be selected after timeout | Passed |
| Stop h5 while h3 is active | h3 should be selected after timeout | Passed |
| Stop both service servers | Discovery should return `NOT_FOUND` after registrations expire | Passed |
| Restart the service servers | Registration and discovery should work again | Passed |

The service registry timeout was configured as 8 seconds. Tests allowed approximately 10 seconds after stopping a service server before checking the result.

### 6.4 Performance evaluation

The performance test was run with 20 discovery requests. One previously recorded run produced the following values:

| Metric | Recorded result |
|---|---:|
| Total requests | 20 |
| Successful requests | 20 |
| Failed requests | 0 |
| Average discovery latency | 1.575 ms |
| Throughput | 601.416 successful requests/second |
| Success rate | 100% |

These are observed values from a particular run and may vary with system load and execution environment. The performance script measures the discovery response, not the full end-to-end service processing time.

### 6.5 OpenFlow verification

The OVS configuration was inspected using `ovs-vsctl show`. The bridge protocol was checked and returned `[OpenFlow13]`. The flow table was inspected using `ovs-ofctl -O OpenFlow13 dump-flows s1`; forwarding entries and packet/byte counters were observed after traffic was generated.

### 6.6 Wireshark packet capture

Wireshark was used to capture traffic on a Mininet switch-facing interface. The following display filters were used:

- `udp.port == 5000` — discovery, registration, and heartbeat traffic.
- `udp.port == 5001` — service request and response traffic.
- `tcp.port == 6653` — OpenFlow controller-switch connection.

Capturing on an individual interface shows traffic visible on that interface; a single host-facing port does not represent all traffic in the topology.

## 7. Limitations and Future Enhancements

1. The topology uses one OVS switch; alternate-path routing and multi-switch failover are not implemented.
2. Round Robin distributes requests cyclically and does not consider CPU load, memory use, or server response time.
3. The Calculator service is a demonstration endpoint that returns a status response; actual arithmetic operations can be added as a future enhancement.
4. The second client host is present in the topology, while the recorded functional and performance tests primarily use h1.
5. Authentication and encryption for application messages are not included.
6. Further experiments could compare Round Robin with random, least-connections, or load-aware selection.

## 8. Conclusion

Basic UDP service-discovery system is used to support multiple service instances in a Mininet SDN environment. The implementation demonstrates service registration, heartbeat-based availability tracking, Round Robin selection, fallback after a service-server failure, a `NOT_FOUND` response when no service instance is active, and recovery after restart. The performance test provides quantitative measurements, while Wireshark and OpenFlow flow-table inspection provide evidence of network communication and SDN forwarding. The results demonstrate the main objectives of the extended service-discovery prototype.

