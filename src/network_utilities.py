import socket
from twisted.application import internet
from twisted.spread import pb
import pickle
from src import protocols


# Returns internet facing IP. Might not work without internet? But works on both linux and Windows while others did not.
def get_local_ip_address():
    internet = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    internet.connect(("8.8.8.8", 80))
    return internet.getsockname()[0]


# Discovers all available shares on the lan
def find_lan_shares() -> str:
    discovery_protocol = protocols.NetworkDiscoveryProtocol()
    server = internet.UDPServer(7999, discovery_protocol)
    server.startService()
    print("Searching for Lan Shares")

    return discovery_protocol.available_shares


class Message:
    def __init__(self, msg_type: str):
        super().__init__()
        self.mType = msg_type

    def encode_msg(self):
        return pickle.dumps(self)


class AuthenticationResponse(Message):
    def __init__(self, share_password: str, username:str, user_password: str):
        super().__init__("AUTH_SYN")
        self.share_password = share_password
        self.username = username
        self.user_password = user_password
        self.sender = get_local_ip_address()


class AuthenticationRequest(Message):
    def __init__(self):
        super().__init__("AUTH_REQ")


def decode_msg(msg) -> Message:
    return pickle.loads(msg)


class MessageCopy(Message, pb.Copyable):
    pass


