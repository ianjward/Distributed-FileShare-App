import glob
import os
from twisted.internet.task import deferLater
from twisted.protocols.amp import AMP
from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileModifiedEvent
import src.utilities.networking
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from src.network_traffic_types.ftp_commands import ServeFile
from src.network_node_types.ftp_node import create_ftp_server, FTPClientCreator
from src.network_traffic_types.master_cmds import UpdateFile, SeedFile
from src.network_traffic_types.slave_cmds import RequestAuth, AuthAccepted, OpenTransferServer
from src.utilities.file_manager import ShareFile, monitor_file_changes


class SlaveProtocol(AMP):
    def connectionMade(self):
        self.updating_file = False
        self.master_ip = self.factory.master_ip
        self.port = self.factory.port
        self.share_name = self.factory.share_name
        self.file_directory = self.factory.file_directory
        self.files = self.factory.files
        self.open_transfer_server()
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
                share_file = ShareFile(file)
                self.files.append(share_file)
                self.callRemote(SeedFile, encoded_file=share_file.encode(), sender_ip=self.get_local_ip())
                print('SLAVE: Seeding file', share_file.file_name)

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
            share_file = ShareFile(file)
            self.files.append(share_file)
            update = self.callRemote(UpdateFile, encoded_file=share_file.encode(), sender_ip=self.get_local_ip())
            update.addCallback(self.update_file, share_file)
            print('SLAVE: Updating file', share_file.file_name)

        # @TODO figure out how to batch events
        monitor_file_changes(self)

    def update_file(self, updated_files, file: ShareFile):
        file_statuses = updated_files['update_ips']
        statuses = file_statuses.split(' ')
        chunks = {}
        ips = set()
        self.updating_file = True
        i = 0

        # Sort uptodate files from outofdate files
        for status in statuses:
            if status != 'current' and status != '':
                chunks[i] = status
                i += 1

        # Connect to nodes with chunk if there are changes to make
        if bool(chunks):
            # Get unique set of ips to connect to for updates
            for value in chunks.values():
                ips.add(value)

            # Connect to each needed update node
            for ip in ips:
                client = FTPClientCreator(ip, 8000)
                client.start_connect()
                deferLater(reactor, 1, self.connect_to_ftp, client, chunks, ip, 0, file)

    def connect_to_ftp(self, client, chunks: dict, ip: str, attempts: int, file: ShareFile):
        file_server = client.factory.distant_end

        # Attempt to reconnect to ftp server
        if file_server is None and attempts < 5:
            client.start_connect()
            attempts += 1
            deferLater(reactor, 1, self.connect_to_ftp, client, chunks, ip, attempts, file)

        # Update chunks w/ ftp server
        if file_server is not None:
            self.update_chunks(file_server, chunks, ip, file)

        # Give up on ftp server connection after 5 tries
        if attempts > 5:
            print('SLAVE: Could not update', file.file_name, 'no connection to', ip)

        self.updating_file = False

    def update_chunks(self, file_server, chunks: dict, ip:str, file: ShareFile):
        for key, value in chunks.items():
            if value == ip:
                updated_chunk = file_server.callRemote(ServeFile, encoded_file=file.encode(), chunk_needed=key)
                updated_chunk.addCallback(self.write_chunks)

    def write_chunks(self, message:dict):
        print("writing chunks")

    def open_transfer_server(self):
        deferred = create_ftp_server(8000)
        return {}
    OpenTransferServer.responder(open_transfer_server)

    def connection_lost(self, node, reason):
        print("SLAVE:", "Connection lost", reason)

    def get_local_ip(self):
        return src.utilities.networking.get_local_ip_address()

    def file_created(self, event: FileCreatedEvent):
        print(event.src_path, event.event_type)

    def file_deleted(self, event: FileDeletedEvent):
        print(event.src_path, event.event_type)

    def file_modified(self, event: FileModifiedEvent):
        print(event.src_path, event.event_type)
        # if not self.updating_file:
        #     self.update_file(event.src_path)


class SlaveNode(ClientFactory):
    protocol = SlaveProtocol

    def __init__(self, port: int, server_ip: str, name: str):
        self.master_ip = server_ip
        self.port = port
        self.share_name = name
        self.file_directory = os.path.join('monitored_files', name)
        self.files = []

        reactor.connectTCP(server_ip, port, self)


