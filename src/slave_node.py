from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from src.protocols import SlaveProtocol
from src.network_utilities import Message, AuthenticationResponse


class SlaveNode(ClientFactory):
    protocol = SlaveProtocol

    def __init__(self, port: int, server_ip: str):
        self.ip = server_ip
        self.master_conn = reactor.connectTCP(server_ip, port, self)

    def new_connection_made(self, protocol:SlaveProtocol):
        print("SLAVE: Talking to share master")

    def receive_msg(self, msg:Message, protocol:SlaveProtocol):
        m_type = msg.mType

        if m_type == 'AUTH_REQ':
            self.authenticate(protocol)
        elif m_type == 'something':
            print('someothermessage')

    def authenticate(self, protocol:SlaveProtocol):
        print("SLAVE: Sending Authentication Info")
        response = AuthenticationResponse("1234", "linuxuser ", "supersecretpassword")
        protocol.sendMessage(response)

    def connection_lost(self, node, reason):
        print("Slave: ", "Connection lost", reason)

    def create_file(self):
        file = open("test.txt", "w+")
        file.write("hello world")
        file.close()
        print("gggg")