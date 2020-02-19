# Handles the initial network discovery for now
from _socket import SOL_SOCKET, SO_BROADCAST
import netifaces as netifaces
from twisted.internet.protocol import DatagramProtocol
from twisted.application import internet
from twisted.protocols.policies import TimeoutMixin
import socket


# Might not work without internet? But works on both linux and Windows while others did not.
# def get_ip():
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     s.connect(("8.8.8.8", 80))
#     return s.getsockname()[0]


# For discovering all the available shares on a network and sending out available share ip's to those looking for them.
class NetworkDiscoveryProtocol(DatagramProtocol, TimeoutMixin):
    def startProtocol(self):
        self.transport.socket.setsockopt(SOL_SOCKET, SO_BROADCAST, True)
        self.state = "SEEKING_SHARES"
        self.available_shares = "192.168.1.106 172.1.2.101"  # Just keeping them as a string to make encoding easier
        self.setTimeout(3)  # Waits 3 seconds
        self.sendDatagram()

    def sendDatagram(self):
        # Broadcast a request for all Share ip's
        datagram = str.encode("Irrelevant message text")
        self.transport.write(datagram, ('255.255.255.255', 7999))

    def datagramReceived(self, datagram, host: tuple):
        sender = host[0]

        # If idle, send Share ip's to a requesting computer
        if self.state == "IDLE" and self.sender_is_valid(sender):
            print("Received Share ip request from: " + str(host[0]))
            self.transport.write(str.encode(self.available_shares), (host[0], 7999))
            print("Responded to ", str(host[0]), " with ", self.available_shares)

        # Receive Share ip's from a networked computer
        if self.state == "SEEKING_SHARES" and self.sender_is_valid(sender):
            print('Datagram received: ', repr(datagram))
            self.state = "IDLE"

    # Ensures sender isn't the local host
    def sender_is_valid(self, sender:str) -> bool:
        local_ips = []

        # Gets computer's local network interfaces and puts them in a list
        for interface in netifaces.interfaces():
            interface_details = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in interface_details:
                verbose_address = interface_details[netifaces.AF_INET]
                local_ips.append(verbose_address[0]["addr"])

        # Sender is invalid if it is a local ip interface
        if sender in local_ips:
            return False
        return True

    def timeoutConnection(self):
        self.state = "IDLE"
        print("Network discovery timed out, state set to IDLE")


# Discovers all available shares on the lan
def find_local_shares() -> NetworkDiscoveryProtocol:
    network_discovery = NetworkDiscoveryProtocol()
    server = internet.UDPServer(7999, network_discovery)
    print("Searching for Lan Shares")
    server.startService()

    return network_discovery
    # server.stopService()
