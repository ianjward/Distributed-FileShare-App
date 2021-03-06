import os
from pathlib import Path
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint
from twisted.protocols.amp import AMP
import src.utilities.networking
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from src.utilities.file_manager import decode_file
from src.network_traffic_types.master_cmds import UpdateFile, SeedFile, GetFileList, DeleteFile, CreateMasterFile, \
    CheckTrackingFile, PullFile, Test, PushFile
from src.network_traffic_types.broadcast_msgs import MasterUpdateMsg
from src.network_traffic_types.slave_cmds import RequestAuth, AuthAccepted, OpenTransferServer, DeleteSlaveFile, CreateFile
from os import listdir


def cmp_floats(a: float, b: float) -> bool:
    epsilon = .00001
    return True if a - b > epsilon else False


class MasterProtocol(AMP):

    # Handles new slave connection
    def connectionMade(self):
        self.dist_ip = self.factory.ip

        print("MASTER: New connection detected!")
        print("MASTER: Requesting authentication")

        self.update_broadcasted_shares()
        self.request_auth()

    # Connect timout error handler
    def print_error(self, error):
        print(error)

    # Ensures broadcast is sending out the next available port to authenticate w/ master on
    def update_broadcasted_shares(self):
        shares = self.factory.broadcast_proto.available_shares
        self.factory.nxt_open_port += 1
        self.factory.open_new_port()

        shares[self.factory.name] = (self.factory.nxt_open_port, self.factory.ip)
        msg = MasterUpdateMsg(shares)
        self.factory.broadcast_proto.send_datagram(msg)

    # Makes slave authenticate before joining
    def request_auth(self):
        request = self.callRemote(RequestAuth)
        request.addCallback(self.check_creds)
        request.addErrback(self.print_error)

    # Tells slave if master is currently tracking a file
    def is_tracking(self, file_name):
        if file_name in self.factory.tracked_files.keys():
            return{'is_tracking': 'True'}
        else:
            return{'is_tracking': 'False'}
    CheckTrackingFile.responder(is_tracking)

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

    # Adds a file to master and then pushes to slaves
    def create_file(self, encoded_file, sender_ip):
        file = decode_file(encoded_file)
        self.seed_file(encoded_file, sender_ip)
        for slave in self.factory.endpoints.values():
            slave.callRemote(CreateFile, encoded_file=file.encode())
        return {}
    CreateMasterFile.responder(create_file)

    # Checks if file is uptodate provides slave w/appropriate action based on updatedness
    def update_file(self, encoded_file, sender_ip):
        file = decode_file(encoded_file)
        file_name = file.file_name
        hashes = file.chunk_hashes
        ips = ''
        chnks_to_update = ''
        chnk_indx = 0
        sync_actn = 'pull'
        mstr_has_file = True
        mstrfile_mtchs_sntfile = False

        # Track any files this master has never seen before
        if file_name not in self.factory.tracked_files:
            self.seed_file(encoded_file, sender_ip)
            mstr_has_file = False

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

            # Choose file data to store
            try:
                if stored_hashes[chnk_indx] != hashes[chnk_indx]:
                    stored_timestmp[chnk_indx] = stored_timestmp[chnk_indx] if mstr_file_curr else file.last_mod_time
                    stored_hashes[chnk_indx] = stored_hashes[chnk_indx] if mstr_file_curr else file.sha1_hash
                    stored_ips[chnk_indx] = stored_ips[chnk_indx] if mstr_file_curr else file.addresses[chnk_indx]
            except:
                stored_timestmp[chnk_indx] = stored_timestmp[chnk_indx]
                stored_hashes[chnk_indx] = stored_hashes[chnk_indx]
                stored_ips[chnk_indx] = stored_ips[chnk_indx]
                mstr_file_curr = True
                mstrfile_mtchs_sntfile = False
                while chnk_indx < stored_num_chnks-1:
                    chnks_to_update += str(chnk_indx) + ' '
                    chnk_indx += 1

            # Signal slave to push file
            if not mstr_file_curr and not mstrfile_mtchs_sntfile:
                sync_actn = 'push'
            elif mstr_file_curr and not mstrfile_mtchs_sntfile:
                sync_actn = 'pull'

            chnks_to_update += str(chnk_indx) + ' '
            chnk_indx += 1

        print('MASTER: Stored file', file_name, 'is current:', mstr_file_curr)

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

    def pull_file(self, encoded_file, sender_ip):
        file = decode_file(encoded_file)
        file_name = file.file_name
        stored_ips = self.factory.tracked_files[file_name][1][0]
        stored_num_chnks = len(stored_ips)
        chnk_indx = 0
        chnks_to_update = ''
        sync_actn = 'pull'

        while chnk_indx < stored_num_chnks:
            chnks_to_update += str(chnk_indx) + ' '
            chnk_indx += 1
        ip = stored_ips[0]
        return {'ips':ip, 'chnks': chnks_to_update, 'actn': sync_actn}
    PullFile.responder(pull_file)

    # Force updates a file the master is tracking
    def push_file(self, encoded_file, sender_ip):
        file = decode_file(encoded_file)
        file_name = file.file_name
        stored_ips = self.factory.tracked_files[file_name][1][0]
        stored_num_chnks = len(stored_ips)
        chnk_indx = 0
        chnks_to_update = ''
        sync_actn = 'push'

        # Add appended chunks
        while chnk_indx < stored_num_chnks:
            chnks_to_update += str(chnk_indx) + ' '
            chnk_indx += 1
        ip = self.dist_ip

        # Ensure enpoint is up todate
        if sender_ip == self.dist_ip:
            ip = list(self.factory.endpoints.keys())[1]
        return {'ips':ip, 'chnks': chnks_to_update, 'actn': sync_actn}
    PushFile.responder(push_file)

    def delete_file(self, file_name):
        try:
            self.factory.tracked_files.pop(file_name)
            print('MASTER: Stopped tracking', file_name)
            for slave in self.factory.endpoints.values():
                slave.callRemote(DeleteSlaveFile, file_name=file_name)
        except:
            print('MASTER: Removed', file_name)
        return {}
    DeleteFile.responder(delete_file)

    # Returns a list of all files master is tracking
    def get_file_list(self):
        files = ''
        root_path = os.path.normpath(os.getcwd() + os.sep + os.pardir)
        path = os.path.join(root_path, 'src', 'monitored_files', 'ians_share')

        for file in listdir(path):
            files += Path(file).name + ' '
        return {'files': files}
    GetFileList.responder(get_file_list)


# Creates master protocols
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










