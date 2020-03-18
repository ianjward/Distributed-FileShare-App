from _socket import SOL_SOCKET, SO_BROADCAST
from enum import Enum
import netifaces as netifaces
from twisted.internet.protocol import DatagramProtocol, Protocol
from twisted.protocols.policies import TimeoutMixin
from src.utilities.network_utilities import get_local_ip_address
from src.utilities.messages import decode_msg, Message


class State (Enum):
    NEEDS_IPS = 'SEEKING_SHARES'
    HAS_IPS = 'IDLE'


class NetworkDiscoveryProtocol(DatagramProtocol, TimeoutMixin):

    def startProtocol(self):
        self.transport.socket.setsockopt(SOL_SOCKET, SO_BROADCAST, True)
        self.state = State.NEEDS_IPS
        self.available_shares = str(get_local_ip_address())  # Just keeping them as a string to make encoding easier
        self.setTimeout(3)  # Waits 3 seconds
        self.sendDatagram()

    def sendDatagram(self):
        broadcast_port = 7999
        broadcast_ip = '255.255.255.255'
        msg = Message("Send available LAN share IP's")

        # Broadcast a request for all Share ip's
        self.transport.write(msg.encode_msg(), (broadcast_ip, broadcast_port))

    def datagramReceived(self, encoded_msg, host:tuple):
        sender = host[0]

        # If idle, send Share ip's to a requesting computer
        if self.state == State.HAS_IPS and self.sender_is_valid(sender):
            response = Message(self.available_shares).encode_msg()
            self.transport.write(response, (sender, 7999))
            print("Received Share ip request from: " + str(sender))
            print("Responded to ", str(sender), " with ", self.available_shares)

        # Receive Share ip's from a networked computer
        if self.state == State.NEEDS_IPS and self.sender_is_valid(sender):
            print('Message received: ', decode_msg(encoded_msg))
            self.state = State.HAS_IPS

    # Ensures sender isn't the local host
    def sender_is_valid(self, sender:str) -> bool:
        self_ips = []

        # Gets computer's local network interfaces and puts them in a list
        for interface in netifaces.interfaces():
            interface_details = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in interface_details:
                verbose_address = interface_details[netifaces.AF_INET]
                self_ips.append(verbose_address[0]["addr"])

        # Sender is invalid if it is a local ip interface
        if sender in self_ips:
            return False
        return True

    def timeoutConnection(self):
        self.state = State.HAS_IPS
        print("Network discovery timed out, assuming no available shares.")


class SlaveProtocol(Protocol):
    def connectionMade(self):
        self.factory.new_connection_made(self)

    def dataReceived(self, encoded_msg):
        msg = decode_msg(encoded_msg)
        self.factory.receive_msg(msg, self)

    def clientConnectionLost(self, connector, reason):
        self.factory.connection_lost(self, reason)

    def sendMessage(self, msg: Message):
        encoded_msg = msg.encode_msg()
        self.transport.write(encoded_msg)


class MasterProtocol(Protocol):
    def connectionMade(self):
        self.factory.new_connection_made(self)

    def connectionLost(self, reason):
        self.factory.connection_lost(self, reason)

    def dataReceived(self, encoded_msg):
        msg = decode_msg(encoded_msg)
        self.factory.receive_msg(msg, self)

    def sendMessage(self, msg:Message):
        encoded_msg = msg.encode_msg()
        self.transport.write(encoded_msg)



