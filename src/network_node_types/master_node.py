from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint
from twisted.protocols.amp import AMP
from twisted.python.log import err

import src.utilities.networking
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from src.utilities.file_manager import decode_file
from src.network_traffic_types.master_cmds import SeedFile
from src.network_traffic_types.broadcast_msgs import MasterUpdateMsg
from src.network_traffic_types.slave_cmds import RequestAuth, AuthAccepted


class MasterProtocol(AMP):
    def connectionMade(self):
        print("MASTER: New connection detected!")
        print("MASTER: Requesting authentication")
        # deferLater(reactor, 1, self.simpleSub, 5, 2)

        self.update_broadcasted_shares()
        self.request_auth()

    def update_broadcasted_shares(self):
        shares = self.factory.broadcast_proto.available_shares
        self.factory.nxt_open_port += 1
        self.factory.open_new_port()

        shares[self.factory.name] = (self.factory.nxt_open_port, self.factory.ip)
        msg = MasterUpdateMsg(shares)
        self.factory.broadcast_proto.send_datagram(msg)

    def request_auth(self):
        request = self.callRemote(RequestAuth)
        request.addCallback(self.check_creds)
        request.addErrback(self.print_error)

    def check_creds(self, creds:dict):
        if creds['share_password'] == self.factory.access_code:
            print("MASTER: Authenticated:", creds['username'], creds['user_password'])
            self.callRemote(AuthAccepted)

    def seed_file(self, encoded_file, sender_ip):
        file = decode_file(encoded_file)
        file_name = file.file_name
        chunks = file.chunks
        chunk_ips = []

        for _ in chunks:
            chunk_ips.append(sender_ip)
            self.factory.tracked_files[file_name] = (chunks,chunk_ips)
        print('MASTER: Tracking', self.factory.tracked_files)
        return {}
    SeedFile.responder(seed_file)

    def print_error(self, error):
        print(error)


class MasterNode(Factory):
    protocol = MasterProtocol
    endpoints = []

    def __init__(self, port: int, share_name: str, access_code: str, broadcast_proto):
        self.nxt_open_port = port
        self.users = []
        self.tracked_files = {}  # filename: (chunks[], chunk_ips[])

        self.name = share_name
        # self.uuid = share_name + "_" + datetime.now().strftime("%Y-%m-%d-%H:%M:%S") + "_" + str(uuid.getnode())
        self.access_code = access_code
        self.ip = self.get_local_ip()
        self.file_directory = 'monitored_files/' + share_name + '/'
        self.broadcast_proto = broadcast_proto
        print("MASTER: Started a share on ", self.ip, ":", port)
        self.open_new_port()
        # @TODO move to endpoints again

    def open_new_port(self):
        new_endpoint = reactor.listenTCP(self.nxt_open_port, self)
        self.endpoints.insert(self.nxt_open_port, new_endpoint)  # Need to do after authentication

    def get_local_ip(self):
        return src.utilities.networking.get_local_ip_address()








