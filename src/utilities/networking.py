import netifaces as netifaces
import uuid
from _socket import SOL_SOCKET, SO_BROADCAST
from enum import Enum
from twisted.internet.protocol import DatagramProtocol, Factory, ClientFactory
from twisted.protocols.policies import TimeoutMixin
from src.protocols.master import MasterProtocol
from src.protocols.slave import SlaveProtocol
from src.utilities.messages import *
from datetime import datetime
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.application import internet
from twisted.internet import reactor
from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileModifiedEvent


global discovery_protocol
global wanted_networks


class State(Enum):
    NEEDS_IPS = "needs_ip"


class NetworkDiscoveryProtocol(DatagramProtocol, TimeoutMixin):
    def startProtocol(self):
        self.transport.socket.setsockopt(SOL_SOCKET, SO_BROADCAST, True)
        self.state = "NEEDS_IPS"
        self.available_shares = {}
        self.send_datagram(RequestMastersMsg())
        reactor.callLater(3.5, create_network_node, self)

    def send_datagram(self, msg:Message):
        broadcast_port = 7999
        broadcast_ip = '255.255.255.255'
        self.transport.write(msg.encode_msg(), (broadcast_ip, broadcast_port))

    def datagramReceived(self, encoded_msg, host: tuple):
        msg = decode_msg(encoded_msg)
        sender = host[0]
        valid_sender = sender_is_valid(sender)
        mtype = msg.mType

        if mtype == 'REQST_MSTRS' and valid_sender:
            print("NETWORK: Received msg", msg.mType)
            self.send_master_list(sender)

        elif mtype == 'MSTR_LIST' and valid_sender:
            print("NETWORK: Received msg", msg.mType)
            self.receive_master_list(msg)

    def send_master_list(self, sender:tuple):
        if self.state == "HAS_IPS":
            response = MasterListMsg(self.available_shares).encode_msg()
            self.transport.write(response, (sender, 7999))
            print("Received Share ip request from: " + str(sender))
            print("Responded to ", str(sender), " with ", self.available_shares)

    def receive_master_list(self, msg:MasterListMsg):
        if self.state == "NEEDS_IPS":
            self.available_shares = msg.master_dict
            print('Message received: ', msg.master_dict)
            self.state = "HAS_IPS"


def create_network_node(protocol:NetworkDiscoveryProtocol):
    if protocol.state == 'NEEDS_IPS':
        protocol.state = "HAS_IPS"
        protocol.available_shares["ians_share"] = (3025, get_local_ip_address())
        print("No available shares found.")
        MasterNode(3025, "MyTestShare", '1234')
    else:
        for share in protocol.available_shares:
            join_network(share, protocol.available_shares)


def join_network(share, available_shares):
    # @TODO bump up port by 1 and send update msg on broadcast + readin share name + only join desired
    global wanted_networks
    if share in wanted_networks:
        port = available_shares[share][0]
        master_ip = available_shares[share][1]
        SlaveNode(port, master_ip)


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
        response = AuthNeededMsg()
        protocol.sendMessage(response)

    def receive_msg(self, msg: Message, protocol: MasterProtocol):
        mType = msg.mType
        print("MASTER:", "Msg received")

        if mType == 'AUTH_SYN':
            self.authenticate(msg, protocol)

        elif mType == 'SEND_ALL':
            self.send_all_files(protocol)

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
        elif m_type == 'AUTH_OK':
            self.update_all_share_files(protocol)

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


# Discovers all available shares on the lan
def find_lan_shares(share_names:list):
    global discovery_protocol
    global wanted_networks

    print("Searching for Lan Shares")
    wanted_networks = share_names
    discovery_protocol = NetworkDiscoveryProtocol()
    server = internet.UDPServer(7999, discovery_protocol)
    server.startService()


# Returns internet facing IP. Might not work without internet? But works on both linux and Windows while others did not.
def get_local_ip_address():
    internet = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    internet.connect(("8.8.8.8", 80))
    return internet.getsockname()[0]