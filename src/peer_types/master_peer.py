from datetime import datetime
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from src.utilities.protocols import MasterProtocol
from src.utilities.network_utilities import get_local_ip_address
from src.utilities.messages import Message, AuthenticationRequest
import uuid


class MasterNode(Factory):
    protocol = MasterProtocol

    def __init__(self, port: int, share_name: str, access_code:str):
        print("MASTER: Started a share on ", get_local_ip_address(),":", port)

        self.nodes = []
        self.users = []
        self.files = []
        self.name = share_name
        self.uuid = share_name + "_" + datetime.now().strftime("%Y-%m-%d-%H:%M:%S") + "_" + str(uuid.getnode())
        self.access_code = access_code
        self.ip = get_local_ip_address()

        self.endpoint1 = TCP4ServerEndpoint(reactor, port)
        self.endpoint1.listen(self)

    def new_connection_made(self, protocol:MasterProtocol):
        print("MASTER: New connection detected!")
        print("MASTER: Requesting authentication")
        response = AuthenticationRequest()
        protocol.sendMessage(response)

    def receive_msg(self, msg: Message, protocol:MasterProtocol):
        mType = msg.mType
        print("MASTER:","Msg received")

        if mType == 'AUTH_SYN':
            self.authenticate(msg)

        elif mType == 'something':
            print('someothermessage')

    def authenticate(self, msg):
        if msg.share_password == self.access_code:
            self.nodes.append(msg.username)  # I'm not sure what exactly to put in nodes for now
            print("MASTER: Authenticated:", msg.username, msg.user_password)

    def connection_lost(self, node, reason):
        print("MASTER:", "Connection lost", reason)
        self.nodes.remove(node)





