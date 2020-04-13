from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint
from twisted.protocols.amp import AMP
from twisted.python.log import err
import src.utilities.networking
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from src.utilities.file_manager import decode_file
from src.network_traffic_types.master_cmds import UpdateFile, SeedFile
from src.network_traffic_types.broadcast_msgs import MasterUpdateMsg
from src.network_traffic_types.slave_cmds import RequestAuth, AuthAccepted, OpenTransferServer


def cmp_floats(a: float, b: float) -> bool:
    epsilon = .00001
    return True if abs(a - b) < epsilon else False


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
            port = creds['sender_port']
            ip = creds['sender_ip']
            print("MASTER: Authenticated:", creds['username'], creds['user_password'])
            self.factory.endpoints[ip] = self
            self.callRemote(AuthAccepted)

    def seed_file(self, encoded_file, sender_ip):
        file = decode_file(encoded_file)
        file_name = file.file_name
        hashes = file.chunk_hashes
        chunk_ips = []
        mod_times = []

        # Start tracking each hash in the file
        for _ in hashes:
            chunk_ips.append(sender_ip)
            mod_times.append(file.last_mod_time)
            self.factory.tracked_files[file_name] = (hashes, (chunk_ips, mod_times))
        print('MASTER: Tracking', self.factory.tracked_files)
        return {}
    SeedFile.responder(seed_file)

    def update_file(self, encoded_file, sender_ip):
        file = decode_file(encoded_file)
        file_name = file.file_name
        hashes = file.hash_chunks
        chunks_to_update = ''
        i = 0

        # Track any files master has never seen before
        if file_name not in self.factory.tracked_files:
            self.seed_file(encoded_file, sender_ip)

        # Set stored file info if file is being tracked by master
        stored_ips = self.factory.tracked_files[file_name][1][0]
        num_stored_chunks = len(stored_ips)
        stored_timestamp = self.factory.tracked_files[file_name][1][1]
        stored_hashes = self.factory.tracked_files[file_name][0]
        altered_ips = set()

        # Check new hash against stored hash
        while i < num_stored_chunks:
            stored_is_current = cmp_floats(stored_timestamp[i], file.last_mod_time)
            stored_matches_file = stored_ips[i] == sender_ip

            # Choose latest file data to store
            if stored_hashes[i] != hashes[i]:
                stored_timestamp[i] = stored_timestamp[i] if stored_is_current else file.last_mod_time
                # @TODO is sha1hash right?
                stored_hashes[i] = stored_hashes[i] if stored_is_current else file.sha1_hash
                stored_ips[i] = stored_ips[i] if stored_is_current else file.addresses[i]

            # Append current status to return string if chunk is uptodate
            if stored_is_current or stored_matches_file:
                chunks_to_update += 'current '
                # altered_ips.add(stored_ips[i])

            # Append ip with the uptodate chunk if file is outofdate
            else:
                chunks_to_update += stored_ips[i] + ' '
                altered_ips.add(stored_ips[i])
            i += 1

        # Track any new file chunks
        while i < file.num_chunks:
            chunks_to_update += stored_ips[i] + ' '
            altered_ips.add(stored_ips[i])
            i += 1

        # for ip in altered_ips:
        #     print(self.factory.endpoints)
        #     connection = self.factory.endpoints[ip]
        #     connection.callRemote(OpenTransferServer)
        return {'update_ips': chunks_to_update}
    UpdateFile.responder(update_file)

    def print_error(self, error):
        print(error)


class MasterNode(Factory):
    protocol = MasterProtocol
    endpoints = {}
    ip_to_port_map = {}

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

    def open_new_port(self):
        new_endpoint = TCP4ServerEndpoint(reactor, self.nxt_open_port)
        new_endpoint.listen(self)

    def get_local_ip(self):
        return src.utilities.networking.get_local_ip_address()









