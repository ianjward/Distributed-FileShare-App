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
    CheckTrackingFile, PullFile
from src.network_traffic_types.slave_cmds import RequestAuth, AuthAccepted, OpenTransferServer, DeleteSlaveFile, \
    CreateFile
from src.utilities.file_manager import ShareFile, monitor_file_changes, Chunk
from os import path


class SlaveProtocol(AMP):
    last_mod_time = datetime.now()

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

    def authenticate(self):
        print("SLAVE: Sending authentication info to master")
        return {'share_password': '1234',
                'username': 'linuxuser',
                'user_password': 'supersecretpassword',
                'sender_ip': self.get_local_ip(),
                'sender_port': self.port}
    RequestAuth.responder(authenticate)

    def initialize_files(self):
        print("SLAVE: Received auth ok")

        # Seed files the master is tracking if master is at same ip
        if self.get_local_ip() == self.master_ip:
            path_to_files = os.path.join(self.file_directory, '*')
            file_locations = glob.glob(path_to_files)

            # Seed each file
            for file in file_locations:
                share_file = ShareFile(file, self.share_name)
                self.files.append(share_file)
                self.callRemote(SeedFile, encoded_file=share_file.encode(), sender_ip=self.get_local_ip())
                print('SLAVE: Seeding file', share_file.file_name)
            monitor_file_changes(self)

        # Update instead of Seed files w/master
        else:
            self.update_all_share_files()

        return {}
    AuthAccepted.responder(initialize_files)

    def update_all_share_files(self):
        path_to_files = os.path.join(self.file_directory, '*')
        file_locations = glob.glob(path_to_files)

        # Update each file
        for file in file_locations:
            share_file = ShareFile(file, self.share_name)
            self.files.append(share_file)
            update = self.callRemote(UpdateFile, encoded_file=share_file.encode(), sender_ip=self.get_local_ip())
            update.addCallback(self.update_file, share_file)
            print('SLAVE: Updating file', share_file.file_name)

        master_files = self.callRemote(GetFileList)
        master_files.addCallback(self.update_untracked_files)
        monitor_file_changes(self)

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
                update = self.callRemote(UpdateFile, encoded_file=share_file.encode(), sender_ip=self.get_local_ip())
                update.addCallback(self.update_file, share_file)
                print('SLAVE: Updating file', share_file.file_name)

    def receive_chunk(self, chunk: Chunk):
        file_name = chunk.file.file_name
        chunks_remaining = self.chunks_awaiting_update[file_name] - 1
        self.received_chunks.append(chunk)
        self.chunks_awaiting_update[file_name] -= 1

        # Write to file if all chunks received
        if chunks_remaining == 0:
            print('SLAVE: Received all chunks for', file_name)
            chunk.file.write_chunks(self, file_name)
        self.close_ftp(self.chunks_awaiting_update[file_name], chunk.file)

        deferLater(reactor, 5, self.close_ftp, -1, chunk.file)

    def update_file(self, update_peers, file: ShareFile):
        file.chunks_needed = update_peers['chnks']
        total_chnks = file.chunks_needed.split(' ')
        total_chnks.remove('')
        file.awaiting_chunks = len(total_chnks)
        sync_actn = update_peers['actn']
        ip = update_peers['ips']
        self.updating_file = True

        if self.client is None:
            self.client = FTPClientCreator(ip, 8000, self)
            self.client.start_connect()
        deferLater(reactor, 1, self.connect_to_ftp, self.client, ip, 0, file, sync_actn)

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

    def close_ftp(self, awaiting_chunks: int, file: ShareFile):
        file_name = file.file_name

        if awaiting_chunks == -1 and self.chunks_awaiting_update[file_name] != 0:
            print('SLAVE: Could not update all chunks for', file_name, 'closing ftp connection')
            self.updating_file = False
            self.chunks_awaiting_update[file_name] = 0

        if awaiting_chunks == 0:
            self.received_chunks = []
            self.updating_file = False
            self.chunks_awaiting_update[file_name] = 0
            print('SLAVE: Updated all chunks for', file_name, 'closing ftp connection')
        file.__hash__()

    def open_ftp_server(self):
        create_ftp_server(8000, self)
        return {}
    OpenTransferServer.responder(open_ftp_server)

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

    def create_file(self, file_name):
        root_path = os.path.normpath(os.getcwd() + os.sep + os.pardir)
        file = os.path.join(root_path, 'src', 'monitored_files', 'ians_share', file_name)

        if not path.exists(file):
            self.updating_file = True

            open(file, 'w+')
            share_file = ShareFile(file, self.share_name)
            self.files.append(share_file)

            share_file.last_mod_time = 0
            print('here')
            update = self.callRemote(PullFile, encoded_file=share_file.encode(), sender_ip=self.get_local_ip())
            update.addCallback(self.update_file, share_file)
        return {}
    CreateFile.responder(create_file)

    def file_created(self, event: FileCreatedEvent):
        file_name = Path(event.src_path).name

        if '~' in file_name:
            return

        self.updating_file = True
        time.sleep(1)
        share_file = ShareFile(event.src_path, self.share_name)

        self.files.append(share_file)
        mstr_tracking_file = self.callRemote(CheckTrackingFile, file_name=share_file.file_name)

        mstr_tracking_file.addCallback(self.add_to_master, share_file)

    def add_to_master(self, master_needs_file, share_file: ShareFile):
        print('SLAVE: Created file', share_file.file_name)
        if master_needs_file['is_tracking'] is False:
            print('SLAVE: Adding file to master')
            self.callRemote(CreateMasterFile, encoded_file=share_file.encode(), sender_ip=self.get_local_ip())
        self.updating_file = False

    def file_deleted(self, event: FileDeletedEvent):
        file_name = Path(event.src_path).name
        if '~' in file_name:
            return
        self.callRemote(DeleteFile, file_name=file_name)

    def file_modified(self, event: FileModifiedEvent):
        file_name = Path(event.src_path).name

        # prevent path only updates
        if '.' not in file_name:
            return

        # prevent temp file updates
        if '~' in file_name:
            return

        if datetime.now() - self.last_mod_time < timedelta(seconds=1):
            return
        if self.updating_file is False:
            self.last_mod_time = datetime.now()
            print(event.src_path, event.event_type)
            share_file = ShareFile(event.src_path, self.share_name)
            update = self.callRemote(UpdateFile, encoded_file=share_file.encode(), sender_ip=self.get_local_ip())
            update.addCallback(self.update_file, share_file)
            print('SLAVE: Updating file', share_file.file_name)


class SlaveNode(ClientFactory):
    protocol = SlaveProtocol

    def __init__(self, port: int, server_ip: str, name: str):
        self.master_ip = server_ip
        self.port = port
        self.share_name = name
        self.file_directory = os.path.join('monitored_files', name)
        self.files = []

        reactor.connectTCP(server_ip, port, self)


