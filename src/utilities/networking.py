import socket
import time
from twisted.application import internet
from src.utilities.protocols import NetworkDiscoveryProtocol


# # Discovers all available shares on the lan
def find_lan_shares() -> str:
    print("Searching for Lan Shares")

    discovery_protocol = NetworkDiscoveryProtocol()
    server = internet.UDPServer(7999, discovery_protocol)
    server.startService()
    time.sleep(6)
    return discovery_protocol.available_shares


# Returns internet facing IP. Might not work without internet? But works on both linux and Windows while others did not.
def get_local_ip_address():
    internet = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    internet.connect(("8.8.8.8", 80))
    return internet.getsockname()[0]


# def getDummyData(x):
#     """
#     This function is a dummy which simulates a delayed result and
#     returns a Deferred which will fire with that result. Don't try too
#     hard to understand this.
#     """
#     d = defer.Deferred()
#     # simulate a delayed result by asking the reactor to fire the
#     # Deferred in 2 seconds time with the result x * 3
#     reactor.callLater(2, d.callback, x * 3)
#     return d
#
# def printData(d):
#     """
#     Data handling function to be added as a callback: handles the
#     data by printing the result
#     """
#     print d
#
# d = getDummyData(3)