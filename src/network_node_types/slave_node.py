import glob
import os
from twisted.internet.task import deferLater
from twisted.protocols.amp import AMP
from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileModifiedEvent
import src.utilities.networking
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from src.network_traffic_types.ftp_cmds import ServeChunks, ReceiveChunk
from src.network_node_types.ftp_node import create_ftp_server, FTPClientCreator
from src.network_traffic_types.master_cmds import UpdateFile, SeedFile
from src.network_traffic_types.slave_cmds import RequestAuth, AuthAccepted, OpenTransferServer
from src.utilities.file_manager import ShareFile, monitor_file_changes, Chunk


# chunks_to_receive = {}


class SlaveProtocol(AMP):
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
        monitor_file_changes(self)

    def receive_chunk(self, chunk: Chunk):
        file_name = chunk.file.file_name
        chunks_remaining = self.chunks_awaiting_update[file_name] - 1
        self.received_chunks.append(chunk)
        self.chunks_awaiting_update[file_name] -= 1
        # Write to file if all chunks received
        if chunks_remaining == 0:
            print('SLAVE: Received all chunks for', file_name)
            chunk.file.write_chunks(self.received_chunks)
        self.close_ftp(self.chunks_awaiting_update[file_name], chunk.file)

        # @TODO close ftp and reset chunks needed
        deferLater(reactor, 5, self.close_ftp, -1, chunk.file)

    def update_file(self, update_peers, file: ShareFile):
        # return {'ips': ips, 'chnks': chnks_to_update, 'actn': sync_actn}
        ips = update_peers['ips'].split(' ')
        file.chunks_needed = update_peers['chnks']
        total_chnks = file.chunks_needed.split(' ')
        total_chnks.remove('')
        file.awaiting_chunks = len(total_chnks)
        sync_actn = update_peers['actn']
        self.updating_file = True

        # Connect to each needed update node
        for ip in ips:
            client = FTPClientCreator(ip, 8000, self)
            client.start_connect()
            deferLater(reactor, 1, self.connect_to_ftp, client, ip, 0, file, sync_actn)

    def connect_to_ftp(self, client, ip: str, attempts: int, file: ShareFile, sync_actn: str):
        file_server = client.factory.distant_end

        # Attempt to reconnect to ftp server
        if file_server is None and attempts < 5:
            client.start_connect()
            attempts += 1
            deferLater(reactor, 1, self.connect_to_ftp, client, ip, attempts, file)

        # Update chunks w/ ftp server
        if file_server is not None and sync_actn == 'pull':
            self.chunks_awaiting_update[file.file_name] = file.awaiting_chunks
            file_server.callRemote(ServeChunks, encoded_file=file.encode(), sender_ip=self.get_local_ip())

        # Give up on ftp server connection after 5 tries
        if attempts > 5:
            print('SLAVE: Could not update', file.file_name, 'no connection to', ip)

    def close_ftp(self, awaiting_chunks: int, file: ShareFile):
        file_name = file.file_name

        if awaiting_chunks == -1 and self.chunks_awaiting_update[file_name] != 0:
            print('SLAVE: Could not update all chunks for', file_name, 'closing ftp connection')
            self.updating_file = False
            self.chunks_awaiting_update[file_name] = 0
            # @TODO close connection here

        if awaiting_chunks == 0:
            self.updating_file = False
            self.chunks_awaiting_update[file_name] = 0
            print('SLAVE: Updated all chunks for', file_name, 'closing ftp connection')
            # @TODO close connection here
        file.__hash__()

    def open_ftp_server(self):
        create_ftp_server(8000)
        return {}
    OpenTransferServer.responder(open_ftp_server)

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


