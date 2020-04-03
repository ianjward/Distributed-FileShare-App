import glob
import os
from twisted.protocols.amp import AMP
from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileModifiedEvent
import src.utilities.networking
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from src.network_traffic_types.master_cmds import SeedFile, UpdateFile
from src.network_traffic_types.slave_cmds import RequestAuth, AuthAccepted
from src.utilities.file_manager import ShareFile, monitor_file_changes


class SlaveProtocol(AMP):
    def connectionMade(self):
        self.master_ip = self.factory.master_ip
        self.port = self.factory.port
        self.share_name = self.factory.share_name
        self.file_directory = self.factory.file_directory
        self.files = self.factory.files
        print("SLAVE: Talking to Master at", self.master_ip, ':', self.factory.port)

    def authenticate(self):
        print("SLAVE: Sending authentication info to master")
        return {'share_password': '1234',
                'username': 'linuxuser',
                'user_password': 'supersecretpassword'}
    RequestAuth.responder(authenticate)

    def initialize_files(self):
        print("SLAVE: Received auth ok")

        # If first node on share, push all files to master
        if self.master_ip == self.get_local_ip():
            self.seed_master_files()
        else:
            self.update_all_share_files()
        return {}
    AuthAccepted.responder(initialize_files)

    def seed_master_files(self):
        path_to_files = os.path.join(self.file_directory, '*')
        file_locations = glob.glob(path_to_files)

        for file in file_locations:
            share_file = ShareFile(file)
            self.files.append(share_file)

            self.files.append(share_file)
            print('SLAVE: Seeding Master with', share_file.file_name)
            self.callRemote(SeedFile, encoded_file=share_file.encode(), sender_ip=self.get_local_ip())

    def update_all_share_files(self):
        path_to_files = os.path.join(self.file_directory, '*')
        file_locations = glob.glob(path_to_files)

        for file in file_locations:
            share_file = ShareFile(file)
            self.files.append(share_file)
            self.callRemote(UpdateFile, encoded_file=share_file.encode(), sender_ip=self.get_local_ip())
            print('SLAVE: Checking file', share_file.file_name)

    # @TODO figure out how to batch events
        monitor_file_changes(self)

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


class SlaveNode(ClientFactory):
    protocol = SlaveProtocol

    def __init__(self, port: int, server_ip: str, name: str):
        self.master_ip = server_ip
        self.port = port
        self.share_name = name
        self.file_directory = os.path.join('monitored_files', name)
        self.files = []

        reactor.connectTCP(server_ip, port, self)


