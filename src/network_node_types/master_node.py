import glob
import uuid
import src.utilities.networking
import src.protocols.broadcast
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from datetime import datetime
from twisted.internet.protocol import Factory
from src.protocols.master import MasterProtocol
from src.utilities.file_manager import ShareFile
from src.utilities.messages import AuthNeededMsg, Message, MasterUpdateMsg, SeedMasterMsg


class MasterNode(Factory):
    protocol = MasterProtocol

    def __init__(self, port: int, share_name: str, access_code: str, broadcast_proto):
        print("MASTER: Started a share on ", self.get_local_ip(), ":", port)

        self.endpoints = []
        self.nxt_open_port = port
        self.users = []
        self.tracked_files = {}  # filename: (chunks[], chunk_ips[])

        self.name = share_name
        # self.uuid = share_name + "_" + datetime.now().strftime("%Y-%m-%d-%H:%M:%S") + "_" + str(uuid.getnode())
        self.access_code = access_code
        self.ip = self.get_local_ip()
        self.file_directory = 'monitored_files/' + share_name + '/'
        self.broadcast_proto = broadcast_proto

        # self.initialize_files()
        self.open_new_port()

    def new_connection_made(self, protocol: MasterProtocol):
        print("MASTER: New connection detected!")
        print("MASTER: Requesting authentication")
        response = AuthNeededMsg()
        protocol.sendMessage(response)
        self.update_broadcasted_shares()

    def update_broadcasted_shares(self):
        shares = self.broadcast_proto.available_shares
        self.nxt_open_port += 1
        self.open_new_port()

        shares[self.name] = (self.nxt_open_port, self.get_local_ip())
        msg = MasterUpdateMsg(shares)
        self.broadcast_proto.send_datagram(msg)

    def open_new_port(self):
        new_endpoint = TCP4ServerEndpoint(reactor, self.nxt_open_port)
        new_endpoint.listen(self)
        self.endpoints.insert(self.nxt_open_port, new_endpoint)  # Need to do after authentication

    def receive_msg(self, msg: Message, protocol: MasterProtocol):
        mType = msg.mType
        print("MASTER:", "Msg received")

        if mType == 'AUTH_SYN':
            self.authenticate(msg, protocol)
        elif mType == 'SEND_ALL':
            self.send_all_files(protocol)
        elif mType == 'SEED_MSTR':
            self.initialize_files(msg)

    def authenticate(self, msg, protocol: MasterProtocol):
        if msg.share_password == self.access_code:
            print("MASTER: Authenticated:", msg.username, msg.user_password)
            response = Message("AUTH_OK")
            protocol.sendMessage(response)

    def connection_lost(self, node, reason):
        print("MASTER:", "Connection lost", reason)

    def send_all_files(self, protocol: MasterProtocol):
        print('MASTER: Gathering all files')

    def initialize_files(self, msg:SeedMasterMsg):
        file_name = msg.file_name
        chunks = msg.chunks
        chunk_ips = []
        for _ in chunks:
            chunk_ips.append(msg.sender_ip)

        self.tracked_files[file_name] = (chunks,chunk_ips)
        print('MASTER: Tracking', self.tracked_files)

    def get_local_ip(self):
        return src.utilities.networking.get_local_ip_address()
