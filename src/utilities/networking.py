# import socket
import time

from twisted.application import internet
from src.utilities.protocols import NetworkDiscoveryProtocol


# # Discovers all available shares on the lan
def find_lan_shares() -> str:
    discovery_protocol = NetworkDiscoveryProtocol()
    server = internet.UDPServer(7999, discovery_protocol)
    server.startService()
    print("Searching for Lan Shares")

    while True:
        print(discovery_protocol.state)
        if discovery_protocol.state == "HAS_IPS":
            return discovery_protocol.available_shares


