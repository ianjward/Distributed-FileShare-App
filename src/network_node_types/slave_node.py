import sys
import traceback
from _datetime import datetime, timedelta
import glob
import os
import time
from pathlib import Path
from twisted.internet.task import deferLater
from twisted.protocols.amp import AMP
from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileModifiedEvent
import src.utilities.networking
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from src.network_traffic_types.ftp_cmds import ServeChunks, ReceiveChunk, InitiateServe
from src.network_node_types.ftp_node import create_ftp_server, FTPClientCreator
from src.network_traffic_types.master_cmds import UpdateFile, SeedFile, GetFileList, DeleteFile, CreateMasterFile, \
    CheckTrackingFile, PullFile, Test, PushFile
from src.network_traffic_types.slave_cmds import RequestAuth, AuthAccepted, OpenTransferServer, DeleteSlaveFile, \
    CreateFile
from src.utilities.file_manager import ShareFile, monitor_file_changes, Chunk, decode_file
from os import path

from src.utilities.file_monitor import FileMonitor


# Communicates all local file changes to master node
class SlaveProtocol(AMP):
    last_mod_time = datetime.now()
    file_statuses = {}

    # Initializes slave on connection w/ master
    def connectionMade(self):
        self.master_ip = self.factory.master_ip
        self.port = self.factory.port
        self.share_name = self.factory.share_name
        self.file_directory = self.factory.file_directory
        self.files = self.factory.files
        self.open_ftp_server()
        self.chunks_awaiting_update = {}
        self.updating_file = False
        self.received_chunks = []
        self.client = None

        print("SLAVE: Talking to Master at", self.master_ip, ':', self.factory.port)

    # Validates itself with master
    def authenticate(self):
        print("SLAVE: Sending authentication info to master")
        return {'share_password': '1234',
                'username': 'linuxuser',
                'user_password': 'supersecretpassword',
                'sender_ip': self.get_local_ip(),
                'sender_port': self.port}
    RequestAuth.responder(authenticate)

    # Handles local file changes/syncs
    def file_changed(self, file_name:str, mod_time):
        try:
            file_status = self.file_statuses[file_name][0]
            file_write_time = self.file_statuses[file_name][1]
            time_since_write = mod_time - file_write_time

            if file_status != 'ok' or time_since_write < 10:
                print('SLAVE:',file_name, file_status, time_since_write, 'skipping update')
            if file_status == 'ok' and time_since_write > 10:
                print('SLAVE: Changing file',file_name, time_since_write)
                self.file_statuses[file_name] = ('updating', time.time())
                share_file = ShareFile(file_name, self.share_name)
                share_file.__hash__()
                deferLater(reactor, 1, self.call_remote, share_file)

        except AssertionError:
            _, _, tb = sys.exc_info()
            traceback.print_tb(tb)  # Fixed format
            tb_info = traceback.extract_tb(tb)
            filename, line, func, text = tb_info[-1]
            print('An error occurred on line {} in statement {}'.format(line, text))
            self.update_file_status(file_name)

    # Wrapper for local file changes to be sent to master
    def call_remote(self, share_file):
        try:
            update = self.callRemote(PushFile, encoded_file=share_file.encode(), sender_ip=self.get_local_ip())
            update.addCallback(self.push_file, share_file)
        except AssertionError:
            _, _, tb = sys.exc_info()
            traceback.print_tb(tb)  # Fixed format
            tb_info = traceback.extract_tb(tb)
            filename, line, func, text = tb_info[-1]
            print('An error occurred on line {} in statement {}'.format(line, text))
            self.update_file_status(share_file.file_name)

    # Action taken after receiving dirrection from master about a local file change
    def push_file(self, update_peers, file):
        file.chunks_needed = update_peers['chnks']
        total_chnks = file.chunks_needed.split(' ')
        total_chnks.remove('')
        file.awaiting_chunks = len(total_chnks)
        sync_actn = update_peers['actn']
        if sync_actn == 'pull':
            self.file_statuses[file.file_name] = ('updating', time.time())
        ip = update_peers['ips']
        self.updating_file = True
        try:
            if self.client is None:
                self.client = FTPClientCreator(ip, 8000, self)
                self.client.start_connect()
            deferLater(reactor, 1, self.connect_to_ftp, self.client, ip, 0, file, sync_actn)
        except:
            print('SLAVE: Couldnt start ftp in push')

    # Seeds master with files if first node to join net
    def initialize_files(self):
        print("SLAVE: Received auth ok")

        # Seed files the master is tracking if master is at same ip
        if self.get_local_ip() == self.master_ip:
            path_to_files = os.path.join(self.file_directory, '*')
            file_locations = glob.glob(path_to_files)

            # Seed each file
            for file in file_locations:
                share_file = ShareFile(file, self.share_name)
                self.file_statuses[share_file.file_name] = ('ok', time.time())
                self.files.append(share_file)
                self.callRemote(SeedFile, encoded_file=share_file.encode(), sender_ip=self.get_local_ip())
                print('SLAVE: Seeding file', share_file.file_name)
            monitor_file_changes(self)

        # Update instead of Seed files w/master
        else:
            self.update_all_share_files()
        deferLater(reactor, 1, FileMonitor, self)

        return {}
    AuthAccepted.responder(initialize_files)

    # Updates local/master files upon joining net
    def update_all_share_files(self):
        path_to_files = os.path.join(self.file_directory, '*')
        file_locations = glob.glob(path_to_files)

        # Update each file
        for file in file_locations:
            share_file = ShareFile(file, self.share_name)
            self.file_statuses[share_file.file_name] = ('ok', time.time())
            self.files.append(share_file)
            update = self.callRemote(UpdateFile, encoded_file=share_file.encode(), sender_ip=self.get_local_ip())
            update.addCallback(self.update_file, share_file)
            print('SLAVE: Updating file', share_file.file_name)

        master_files = self.callRemote(GetFileList)
        master_files.addCallback(self.update_untracked_files)

    # Adds any local files master is not tracking on startup
    def update_untracked_files(self, master_dict):
        file_string = master_dict['files']
        mastr_files = file_string.split(' ')
        mastr_files.remove('')

        local_files = []
        root_path = os.path.normpath(os.getcwd() + os.sep + os.pardir)
        path = os.path.join(root_path, 'src', 'monitored_files', 'ians_share')

        for file in os.listdir(path):
            local_files.append(Path(file).name)

        for file in mastr_files:
            if file not in local_files:
                share_file = ShareFile(file, self.share_name)
                self.files.append(share_file)
                self.file_statuses[share_file.file_name] = ('updating', time.time())
                update = self.callRemote(UpdateFile, encoded_file=share_file.encode(), sender_ip=self.get_local_ip())
                update.addCallback(self.update_file, share_file)
                print('SLAVE: Updating file', share_file.file_name)

    # Handles ftp chunk reception
    def receive_chunk(self, chunk: Chunk):
        file_name = chunk.file.file_name
        chunks_remaining = self.chunks_awaiting_update[file_name] - 1
        self.received_chunks.append(chunk)
        # adjust for resent chunks
        if chunks_remaining == -1:
            self.chunks_awaiting_update[file_name] = chunk.chunks_in_file
            chunks_remaining = chunk.chunks_in_file - 1
            
        self.chunks_awaiting_update[file_name] -= 1

        # Write to file if all chunks received
        if chunks_remaining == 0:
            print('SLAVE: Received all chunks for', file_name)
            chunk.file.write_chunks(self, file_name)

        self.close_ftp(self.chunks_awaiting_update[file_name], chunk.file)
        deferLater(reactor, 2, self.update_file_status, file_name)
        deferLater(reactor, 5, self.close_ftp, -1, chunk.file)

    # Updates a single file w/master
    def update_file(self, update_peers, file: ShareFile):
        file.chunks_needed = update_peers['chnks']
        total_chnks = file.chunks_needed.split(' ')
        total_chnks.remove('')
        file.awaiting_chunks = len(total_chnks)
        sync_actn = update_peers['actn']
        if sync_actn == 'pull':
            self.file_statuses[file.file_name] = ('updating', time.time())
        ip = update_peers['ips']
        self.updating_file = True
        try:
            if self.client is None:
                self.client = FTPClientCreator(ip, 8000, self)
                self.client.start_connect()
            deferLater(reactor, 1, self.connect_to_ftp, self.client, ip, 0, file, sync_actn)
        except:
            print('SLAVE: Couldnt start ftp in update')

    # Enables local file changes to be tracked once done receiving a file from remote node
    def update_file_status(self, file_name: str):
        self.file_statuses[file_name] = ('ok', time.time())

    # Connects to a distant node for file transfer
    def connect_to_ftp(self, client, ip: str, attempts: int, file: ShareFile, sync_actn: str):
        file_server = client.factory.distant_end
        # Attempt to reconnect to ftp server
        if file_server is None and attempts < 5:
            self.client.start_connect()
            attempts += 1
            deferLater(reactor, 1, self.connect_to_ftp, self.client, ip, attempts, file)

        # Pull chunks w/ ftp server
        if file_server is not None and sync_actn == 'pull':
            self.chunks_awaiting_update[file.file_name] = file.awaiting_chunks
            file_server.callRemote(ServeChunks, encoded_file=file.encode(), sender_ip=self.get_local_ip())
        # Push chunks w/ ftp server
        elif file_server is not None and sync_actn == 'push':
            file_server.callRemote(InitiateServe, encoded_file=file.encode())
        elif sync_actn == 'none':
            print('SLAVE:', file.file_name, 'up to date no action needed')

        # Give up on ftp server connection after 5 tries
        if attempts > 5:
            print('SLAVE: Could not update', file.file_name, 'no connection to', ip)

    # Severs ftp connection on finish/timeout/max # attempts made
    def close_ftp(self, awaiting_chunks: int, file: ShareFile):
        file_name = file.file_name

        if awaiting_chunks == -1 and self.chunks_awaiting_update[file_name] != 0:
            print('SLAVE:', file_name, 'closing ftp connection')
            self.updating_file = False
            self.chunks_awaiting_update[file_name] = 0

        if awaiting_chunks == 0:
            self.received_chunks = []
            self.updating_file = False
            self.chunks_awaiting_update[file_name] = 0
            print('SLAVE: Updated all chunks for', file_name, 'closing ftp connection')
        file.__hash__()

    # Creates a file server
    def open_ftp_server(self):
        create_ftp_server(8000, self)
        return {}
    OpenTransferServer.responder(open_ftp_server)

    # Tells master to delete a file
    def master_deletion_call(self, file_name):
        root_path = os.path.normpath(os.getcwd() + os.sep + os.pardir)
        file_path = os.path.join(root_path, 'src', 'monitored_files', 'ians_share', file_name)
        if path.exists(file_path):
            os.remove(file_path)
            print('SLAVE: Removed', file_name)
        return {}
    DeleteSlaveFile.responder(master_deletion_call)

    def connection_lost(self, node, reason):
        print("SLAVE:", "Connection lost", reason)

    def get_local_ip(self):
        return src.utilities.networking.get_local_ip_address()

    def create_file(self, encoded_file):
        file = decode_file(encoded_file)
        root_path = os.path.normpath(os.getcwd() + os.sep + os.pardir)
        path_to_file = os.path.join(root_path, 'src', 'monitored_files', 'ians_share', file.file_name)
        print('in creating slave file', file.file_name)
        if not path.exists(path_to_file):
            print('slave missign created file')
            self.file_statuses[file.file_name] = ('updating', time.time())
            self.files.append(file)
            open(path_to_file, 'w').close()
            file.last_mod_time = 0
            update = self.callRemote(UpdateFile, encoded_file=file.encode(), sender_ip=self.get_local_ip())
            update.addCallback(self.update_file, file)
        return {}
    CreateFile.responder(create_file)

    # Event handler for file creation
    def file_created(self, event: FileCreatedEvent):
        file_name = Path(event.src_path).name

        # Avoid adding temp files
        if '~' in file_name:
            return
        temp_file = ShareFile(file_name, self.share_name)
        temp_file.__hash__()
        self.file_statuses[file_name] = ('updating', time.time())
        deferLater(reactor, 2, self.add_to_master, temp_file)

    # Takes appropriate action after adding file to master
    def add_to_master(self, share_file: ShareFile):
        while share_file.chunk_hashes == {}:
            print('SLAVE: Awaiting hash for new file')
            share_file.__hash__()
        print('SLAVE: Adding', share_file.file_name, 'to master')
        self.callRemote(CreateMasterFile, encoded_file=share_file.encode(), sender_ip=self.get_local_ip())
        self.updating_file = False

    # Event handler for locally deleted files
    def file_deleted(self, event: FileDeletedEvent):
        file_name = Path(event.src_path).name
        if '~' in file_name:
            return
        self.callRemote(DeleteFile, file_name=file_name)


# Creates slave nodes
class SlaveNode(ClientFactory):
    protocol = SlaveProtocol

    def __init__(self, port: int, server_ip: str, name: str):
        self.master_ip = server_ip
        self.port = port
        self.share_name = name
        self.file_directory = os.path.join('monitored_files', name)
        self.files = []

        reactor.connectTCP(server_ip, port, self)


