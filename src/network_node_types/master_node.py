import glob
import uuid
import src.utilities.networking
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from datetime import datetime
from twisted.internet.protocol import Factory
from src.protocols.master import MasterProtocol
from src.utilities.file_manager import ShareFile
from src.utilities.messages import AuthNeededMsg, Message


get_local_ip = lambda: src.utilities.networking.get_local_ip_address()


class MasterNode(Factory):
    protocol = MasterProtocol

    def __init__(self, port: int, share_name: str, access_code: str):
        print("MASTER: Started a share on ", get_local_ip(), ":", port)

        self.endpoints = []
        self.nxt_open_port = port
        self.users = []
        self.tracked_files = {}
        self.name = share_name
        self.uuid = share_name + "_" + datetime.now().strftime("%Y-%m-%d-%H:%M:%S") + "_" + str(uuid.getnode())
        self.access_code = access_code
        self.ip = get_local_ip()
        self.file_directory = 'monitored_files/' + share_name + '/'

        self.initialize_files()
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

    def initialize_files(self):
        file_locations = glob.glob(self.file_directory + '*')
        for file in file_locations:
            # with open(file) as f:
            #     print(f.read())
            share_file = ShareFile(file)
            share_file.__hash__()
