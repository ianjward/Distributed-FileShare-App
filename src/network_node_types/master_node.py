import os
from pathlib import Path
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint
from twisted.protocols.amp import AMP
from twisted.python.log import err
import src.utilities.networking
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from src.utilities.file_manager import decode_file
from src.network_traffic_types.master_cmds import UpdateFile, SeedFile, GetFileList
from src.network_traffic_types.broadcast_msgs import MasterUpdateMsg
from src.network_traffic_types.slave_cmds import RequestAuth, AuthAccepted, OpenTransferServer
from os import listdir


def cmp_floats(a: float, b: float) -> bool:
    epsilon = .00001
    return True if a - b > epsilon else False


class MasterProtocol(AMP):

    def connectionMade(self):
        self.dist_ip = self.factory.ip
        print("MASTER: New connection detected!")
        print("MASTER: Requesting authentication")

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
            if ip != self.factory.ip:
                self.dist_ip = ip
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
        hashes = file.chunk_hashes
        ips = ''
        chnks_to_update = ''
        chnk_indx = 0
        sync_actn = 'none'
        mstr_has_file = True
        mstrfile_mtchs_sntfile = False

        # Track any files this master has never seen before
        if file_name not in self.factory.tracked_files:
            self.seed_file(encoded_file, sender_ip)
            mstr_has_file = False
            # @TODO push to all nodes except sender while seeding

        # Set master tracking info for file
        stored_ips = self.factory.tracked_files[file_name][1][0]
        stored_num_chnks = len(stored_ips)
        stored_timestmp = self.factory.tracked_files[file_name][1][1]
        stored_hashes = self.factory.tracked_files[file_name][0]

        # Check new file's hashes against stored master hashes
        while chnk_indx < stored_num_chnks:
            mstr_file_curr = cmp_floats(stored_timestmp[chnk_indx], file.last_mod_time)
            # Check if master file matches the file being updates
            if mstr_has_file:
                mstrfile_mtchs_sntfile = stored_ips[chnk_indx] == sender_ip

            # Choose latest file data to store
            if stored_hashes[chnk_indx] != hashes[chnk_indx]:
                stored_timestmp[chnk_indx] = stored_timestmp[chnk_indx] if mstr_file_curr else file.last_mod_time
                stored_hashes[chnk_indx] = stored_hashes[chnk_indx] if mstr_file_curr else file.sha1_hash
                stored_ips[chnk_indx] = stored_ips[chnk_indx] if mstr_file_curr else file.addresses[chnk_indx]

            print('MASTER: Stored file', file_name, 'is current:', mstr_file_curr)
            # Signal slave to push file
            if not mstr_file_curr and not mstrfile_mtchs_sntfile:
                sync_actn = 'push'
            elif mstr_file_curr and not mstrfile_mtchs_sntfile:
                sync_actn = 'pull'

            chnks_to_update += str(chnk_indx) + ' '
            chnk_indx += 1

        # Track any new file chunks appended to end of file
        while chnk_indx < file.num_chunks:
            chnks_to_update += str(chnk_indx) + ' '
            chnk_indx += 1

        # Add ips to push to
        if sync_actn == 'push':
            for ip in self.factory.endpoints.keys():
                ips += str(ip) + ' '
        # Add ips to pull from
        else:
            ips = self.factory.tracked_files[file_name][1][0][0]
        print('MASTER: Awaiting', sync_actn,'for', file_name, chnks_to_update)
        ip = self.dist_ip
        if sender_ip == self.dist_ip:
            ip = self.factory.ip
        return {'ips': ip, 'chnks': chnks_to_update, 'actn': sync_actn}
    UpdateFile.responder(update_file)

    def print_error(self, error):
        print(error)

    def get_file_list(self):
        files = ''
        root_path = os.path.normpath(os.getcwd() + os.sep + os.pardir)
        path = os.path.join(root_path, 'src', 'monitored_files', 'ians_share')


        for file in listdir(path):
            files += Path(file).name + ' '
        print(files)
        return {'files': files}
    GetFileList.responder(get_file_list)

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









