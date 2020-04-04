from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import ClientFactory, Factory
from twisted.protocols.amp import AMP


class TransferServerProtocol(AMP):
    def connectionMade(self):
        print("FTP SERVER: Created")


class TransferClientProtocol(AMP):
    def connectionMade(self):
        print("FTP CLIENT: Created")


class FTPServer(Factory):
    protocol = TransferServerProtocol


def create_ftp_server(port: int):
    new_endpoint = TCP4ServerEndpoint(reactor, port)
    return new_endpoint.listen(FTPServer())


class FTPClient(ClientFactory):
    protocol = TransferClientProtocol

    def __init__(self, port:int, ip:str):
        reactor.connectTCP(ip, port, self)

