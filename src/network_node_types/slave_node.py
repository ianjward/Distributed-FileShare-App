import glob
import os
import src.utilities.networking
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileModifiedEvent
from src.protocols.slave import SlaveProtocol
from src.utilities.file_manager import ShareFile, start_file_monitor
from src.utilities.messages import Message, AuthenticationResponse, CheckChunksMsg, SeedMasterMsg


class SlaveNode(ClientFactory):
    protocol = SlaveProtocol

    def __init__(self, port: int, server_ip: str, name:str):
        self.master_ip = server_ip
        self.port = port
        self.share_name = name
        self.file_directory = 'monitored_files/' + name + '/'
        self.files = []
        self.master_conn = reactor.connectTCP(server_ip, port, self)

    def new_connection_made(self, protocol: SlaveProtocol):
        print("SLAVE: Talking to Master at", self.master_ip, ':', self.port)

    def receive_msg(self, msg: Message, protocol: SlaveProtocol):
        m_type = msg.mType

        print('SLAVE: Msg received')
        if m_type == 'AUTH_REQ':
            self.authenticate(protocol)

        # If both slave and master push all files without checking to see if files are the latest
        elif m_type == 'AUTH_OK' and self.master_ip == self.get_local_ip():
            self.seed_master_files(protocol)

        # Update all files w/master when authenticated
        elif m_type == 'AUTH_OK':
            self.update_all_share_files(protocol)

    def authenticate(self, protocol: SlaveProtocol):
        print("SLAVE: Sending Authentication Info to master")
        response = AuthenticationResponse("1234", "linuxuser ", "supersecretpassword")
        protocol.sendMessage(response)

    def connection_lost(self, node, reason):
        print("SLAVE:", "Connection lost", reason)

    def seed_master_files(self, protocol:SlaveProtocol):
        print('SLAVE: Seeding Master')
        file_locations = glob.glob(self.file_directory + '*')
        for file in file_locations:
            share_file = ShareFile(file)
            self.files.append(share_file)
            msg = SeedMasterMsg(share_file.file_name, share_file.chunks, share_file.last_mod_time)
            protocol.sendMessage(msg)

    def update_all_share_files(self, protocol: SlaveProtocol):

        file_locations = glob.glob(self.file_directory + '*')
        for file in file_locations:
            share_file = ShareFile(file)
            self.files.append(share_file)
            msg = CheckChunksMsg(share_file.file_name, share_file.chunks)
            print('SLAVE: Checking file', share_file.file_name)
            protocol.sendMessage(msg)
        start_file_monitor(self)

    def file_created(self, event: FileCreatedEvent):
        print(event.src_path, event.event_type)

    def file_deleted(self, event: FileDeletedEvent):
        print(event.src_path, event.event_type)

    def file_modified(self, event: FileModifiedEvent):
        print(event.src_path, event.event_type)

    def get_local_ip(self):
        return src.utilities.networking.get_local_ip_address()
