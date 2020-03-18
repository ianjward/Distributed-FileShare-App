import socket
from twisted.application import internet
from src.utilities import protocols


# Returns internet facing IP. Might not work without internet? But works on both linux and Windows while others did not.
def get_local_ip_address():
    internet = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    internet.connect(("8.8.8.8", 80))
    return internet.getsockname()[0]


# Discovers all available shares on the lan
def find_lan_shares() -> str:
    discovery_protocol = protocols.NetworkDiscoveryProtocol()
    server = internet.UDPServer(7999, discovery_protocol)
    server.startService()
    print("Searching for Lan Shares")

    return discovery_protocol.available_shares







