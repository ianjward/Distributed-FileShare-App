from twisted.protocols.amp import AMP
import src.utilities.networking
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from src.network_traffic_types.slave_cmds import RequestAuth, AuthAccepted


class MasterProtocol(AMP):
    def connectionMade(self):
        print("MASTER: New connection detected!")
        print("MASTER: Requesting authentication")
        # print(self.factory.name)
        # deferLater(reactor, 1, self.simpleSub, 5, 2)

        self.request_auth()
        #     self.update_broadcasted_shares()

    def request_auth(self):
        request = self.callRemote(RequestAuth)
        request.addCallback(self.check_creds)
        request.addErrback(self.print_error)

    def check_creds(self, creds:dict):
        if creds['share_password'] == self.factory.access_code:
            print("MASTER: Authenticated:", creds['username'], creds['user_password'])
            self.callRemote(AuthAccepted)

    def print_error(self, error):
        print(error)


class MasterNode(Factory):
    protocol = MasterProtocol

    def __init__(self, port: int, share_name: str, access_code: str, broadcast_proto):
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

        reactor.listenTCP(port, self)
        print("MASTER: Started a share on ", self.get_local_ip(), ":", port)



    #     # self.initialize_files()
    #     self.open_new_port()
    #


    # def update_broadcasted_shares(self):
    #     shares = self.broadcast_proto.available_shares
    #     self.nxt_open_port += 1
    #     self.open_new_port()
    #
    #     shares[self.name] = (self.nxt_open_port, self.get_local_ip())
    #     msg = MasterUpdateMsg(shares)
    #     self.broadcast_proto.send_datagram(msg)
    #
    # def open_new_port(self):
    #     new_endpoint = TCP4ServerEndpoint(reactor, self.nxt_open_port)
    #     new_endpoint.listen(self)
    #     self.endpoints.insert(self.nxt_open_port, new_endpoint)  # Need to do after authentication
    #
    # def receive_msg(self, msg: Message, protocol: MasterProtocol):
    #     mType = msg.mType
    #     print("MASTER:", "Msg received", mType)
    #
    #     if mType == 'AUTH_SYN':
    #         self.authenticate(msg, protocol)
    #     elif mType == 'SEND_ALL':
    #         self.send_all_files(protocol)
    #     elif mType == 'SEED_MSTR':
    #         self.initialize_files(msg)
    #
    # def authenticate(self, msg, protocol: MasterProtocol):
    #     if msg.share_password == self.access_code:
    #         print("MASTER: Authenticated:", msg.username, msg.user_password)
    #         response = Message("AUTH_OK")
    #         protocol.sendMessage(response)
    #
    # def connection_lost(self, node, reason):
    #     print("MASTER:", "Connection lost", reason)
    #
    # def send_all_files(self, protocol: MasterProtocol):
    #     print('MASTER: Gathering all files')
    #
    # def initialize_files(self, msg:SeedMasterMsg):
    #     file_name = msg.file_name
    #     print(file_name)
    #     chunks = msg.chunks
    #     chunk_ips = []
    #
    #     for _ in chunks:
    #         chunk_ips.append(msg.sender_ip)
    #
    #     self.tracked_files[file_name] = (chunks,chunk_ips)
    #     print('MASTER: Tracking', self.tracked_files)
    #
    def get_local_ip(self):
        return src.utilities.networking.get_local_ip_address()


