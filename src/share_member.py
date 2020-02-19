import socket
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


class MemberProtocol(Protocol):
    def connectionMade(self):
        print("MEMBER: Connecting to share controller")

    def dataReceived(self, data):
        if str(data.decode("ascii")) == "AUTHENTICATE":
            print("MEMBER: Attempting to authenticate w/controller")
            response = "AUTH_SYN " + get_ip() + " 1234" + " linuxuser " + "supersecretpassword"
            self.transport.write(str.encode(response))

    def clientConnectionLost(self, connector, reason):
        print(reason)


class MemberFactory(ClientFactory):
    protocol = MemberProtocol

    def __init__(self, ip:str):
        self.ip = ip


class ShareMember:
    def __init__(self, port: int, server_ip: str):
        factory = MemberFactory(server_ip)
        reactor.connectTCP(server_ip, port, factory)
        reactor.run()


