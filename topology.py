from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

def main():
    net = Mininet(controller=None, switch=OVSSwitch, autoSetMacs=True)
    net.addController("c0", controller=RemoteController,
                      ip="127.0.0.1", port=6653)
    hosts = [
        net.addHost("h1", ip="10.0.0.1/24"),
        net.addHost("h2", ip="10.0.0.2/24"),
        net.addHost("h3", ip="10.0.0.3/24"),
        net.addHost("h4", ip="10.0.0.4/24"),
        net.addHost("h5", ip="10.0.0.5/24"),
    ]
    sw = net.addSwitch("s1", protocols="OpenFlow13", failMode="secure")
    for host in hosts:
        net.addLink(host, sw)
    try:
        net.start()
        print("*** Demo 2: h1/h4 clients, h2 discovery, h3/h5 services")
        CLI(net)
    finally:
        net.stop()

if __name__ == "__main__":
    setLogLevel("info")
    main()
