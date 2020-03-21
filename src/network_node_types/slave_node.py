from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileModifiedEvent
from src.protocols.slave import SlaveProtocol
from src.utilities.messages import Message, AuthenticationResponse


class SlaveNode(ClientFactory):
    protocol = SlaveProtocol

    def __init__(self, port: int, server_ip: str, name:str):
        self.master_ip = server_ip
        self.port = port
        self.share_name = name
        self.master_conn = reactor.connectTCP(server_ip, port, self)

    def new_connection_made(self, protocol: SlaveProtocol):
        print("SLAVE: Talking to Master at", self.master_ip, ':', self.port)

    def receive_msg(self, msg: Message, protocol: SlaveProtocol):
        m_type = msg.mType

        print('SLAVE: Msg received')
        if m_type == 'AUTH_REQ':
            self.authenticate(protocol)
        elif m_type == 'AUTH_OK':
            self.update_all_share_files(protocol)

    def authenticate(self, protocol: SlaveProtocol):
        print("SLAVE: Sending Authentication Info to master")
        response = AuthenticationResponse("1234", "linuxuser ", "supersecretpassword")
        protocol.sendMessage(response)

    def connection_lost(self, node, reason):
        print("SLAVE:", "Connection lost", reason)

    def update_all_share_files(self, protocol: SlaveProtocol):
        response = Message("SEND_ALL")
        protocol.sendMessage(response)
        print('SLAVE: Requesting all files')

    def file_created(self, event: FileCreatedEvent):
        print(event.src_path, event.event_type)

    def file_deleted(self, event: FileDeletedEvent):
        print(event.src_path, event.event_type)

    def file_modified(self, event: FileModifiedEvent):
        print(event.src_path, event.event_type)
