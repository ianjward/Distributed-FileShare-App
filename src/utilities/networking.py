import socket
import netifaces as netifaces
import uuid
from _socket import SOL_SOCKET, SO_BROADCAST
from enum import Enum
from twisted.internet.protocol import DatagramProtocol, Factory, ClientFactory
from twisted.protocols.policies import TimeoutMixin
from src.protocols.master import MasterProtocol
from src.protocols.slave import SlaveProtocol
from src.utilities.messages import decode_msg, AuthenticationRequest, Message, AuthenticationResponse
from datetime import datetime
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.application import internet
from twisted.internet import reactor
from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileModifiedEvent


class State(Enum):
    NEEDS_IPS = "needs_ip"


class NetworkDiscoveryProtocol(DatagramProtocol, TimeoutMixin):
    def startProtocol(self):
        self.transport.socket.setsockopt(SOL_SOCKET, SO_BROADCAST, True)
        self.state = "NEEDS_IPS"
        self.available_shares = ""  # Just keeping them as a string to make encoding easier
        # self.available_shares = str(get_local_ip_address())  # Just keeping them as a string to make encoding easier
        self.sendDatagram()
        reactor.callLater(3.5, create_node, self)

    def sendDatagram(self):
        broadcast_port = 7999
        broadcast_ip = '255.255.255.255'
        msg = Message("Send available LAN share IP's")

        # Broadcast a request for all Share ip's
        self.transport.write(msg.encode_msg(), (broadcast_ip, broadcast_port))

    def datagramReceived(self, encoded_msg, host: tuple):
        sender = host[0]

        # If idle, send Share ip's to a requesting computer
        if self.state == "HAS_IPS" and sender_is_valid(sender):
            response = Message(self.available_shares).encode_msg()
            self.transport.write(response, (sender, 7999))
            print("Received Share ip request from: " + str(sender))
            print("Responded to ", str(sender), " with ", self.available_shares)

        # Receive Share ip's from a networked computer
        if self.state == "NEEDS_IPS" and sender_is_valid(sender):
            self.available_shares = str(decode_msg(encoded_msg))
            print('Message received: ', decode_msg(encoded_msg))
            self.state = "HAS_IPS"


def create_node(protocol:NetworkDiscoveryProtocol):
    if protocol.state == 'NEEDS_IPS':
        protocol.state = "HAS_IPS"
        protocol.available_shares += str(get_local_ip_address())
        print("No available shares found.")
        MasterNode(3025, "MyTestShare", '1234')
    else:
        print(protocol.available_shares)
        SlaveNode(3025, get_local_ip_address())


class MasterNode(Factory):
    protocol = MasterProtocol

    def __init__(self, port: int, share_name: str, access_code: str):
        print("MASTER: Started a share on ", get_local_ip_address(), ":", port)

        self.endpoints = []
        self.nxt_open_port = port
        self.users = []
        self.tracked_files = {}
        self.name = share_name
        self.uuid = share_name + "_" + datetime.now().strftime("%Y-%m-%d-%H:%M:%S") + "_" + str(uuid.getnode())
        self.access_code = access_code
        self.ip = get_local_ip_address()

        new_endpoint = TCP4ServerEndpoint(reactor, port)
        new_endpoint.listen(self)
        self.endpoints.insert(self.nxt_open_port, new_endpoint)  # Need to do after authentication
        self.nxt_open_port += 1

    def new_connection_made(self, protocol: MasterProtocol):
        print("MASTER: New connection detected!")
        print("MASTER: Requesting authentication")
        response = AuthenticationRequest()
        protocol.sendMessage(response)

    def receive_msg(self, msg: Message, protocol: MasterProtocol):
        mType = msg.mType
        print("MASTER:", "Msg received")

        if mType == 'AUTH_SYN':
            self.authenticate(msg, protocol)

        elif mType == 'SEND_ALL':
            self.send_all_files(protocol)

        elif mType == 'something':
            print('someothermessage')

    def authenticate(self, msg, protocol: MasterProtocol):
        if msg.share_password == self.access_code:
            print("MASTER: Authenticated:", msg.username, msg.user_password)
            response = Message("AUTH_OK")
            protocol.sendMessage(response)

    def connection_lost(self, node, reason):
        print("MASTER:", "Connection lost", reason)
        self.endpoints.remove(node)

    def send_all_files(self, protocol: MasterProtocol):
        print('MASTER: Gathering all files')


class SlaveNode(ClientFactory):
    protocol = SlaveProtocol

    def __init__(self, port: int, server_ip: str):
        self.master_ip = server_ip
        self.port = port
        self.master_conn = reactor.connectTCP(server_ip, port, self)

    def new_connection_made(self, protocol: SlaveProtocol):
        print("SLAVE: Talking to Master at", self.master_ip, ':', self.port)

    def receive_msg(self, msg: Message, protocol: SlaveProtocol):
        m_type = msg.mType

        print('SLAVE: Msg received')
        if m_type == 'AUTH_REQ':
            self.authenticate(protocol)
        if m_type == 'AUTH_OK':
            self.update_all_share_files(protocol)
        elif m_type == 'something':
            print('someothermessage')

    def authenticate(self, protocol: SlaveProtocol):
        print("SLAVE: Sending Authentication Info to master")
        response = AuthenticationResponse("1234", "linuxuser ", "supersecretpassword")
        protocol.sendMessage(response)

    def connection_lost(self, node, reason):
        print("SLAVE:", "Connection lost", reason)

    def update_all_share_files(self, protocol: SlaveProtocol):
        response = Message("SEND_ALL")
        protocol.sendMessage(response)
        print('SLAVE: Requesting all files')

    # def create_file(self):
    #     file = open("test.txt", "w+")
    #     file.write("hello world")
    #     file.close()

    def file_created(self, event: FileCreatedEvent):
        print(event.src_path, event.event_type)

    def file_deleted(self, event: FileDeletedEvent):
        print(event.src_path, event.event_type)

    def file_modified(self, event: FileModifiedEvent):
        print(event.src_path, event.event_type)


# Ensures sender isn't the local host
def sender_is_valid(sender: str) -> bool:
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


# # Discovers all available shares on the lan
def find_lan_shares():
    print("Searching for Lan Shares")

    discovery_protocol = NetworkDiscoveryProtocol()
    server = internet.UDPServer(7999, discovery_protocol)
    server.startService()


# Returns internet facing IP. Might not work without internet? But works on both linux and Windows while others did not.
def get_local_ip_address():
    internet = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    internet.connect(("8.8.8.8", 80))
    return internet.getsockname()[0]