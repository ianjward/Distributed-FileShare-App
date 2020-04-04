from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint, connectProtocol
from twisted.internet.protocol import ClientFactory, Factory
from twisted.protocols.amp import AMP


class TransferServerProtocol(AMP):
    def connectionMade(self):
        print("FTP SERVER: Connected to client")


class TransferClientProtocol(AMP):
    def connectionMade(self):
        print("FTP CLIENT: Connected to server")


class FTPServer(Factory):
    protocol = TransferServerProtocol


def create_ftp_client(ip: str, port: int):
    reactor.connectTCP(ip, port, FTPClient())
    # endpoint = TCP4ClientEndpoint(reactor, ip, port)
    # return connectProtocol(endpoint, FTPClient())


def create_ftp_server(port: int):
    new_endpoint = TCP4ServerEndpoint(reactor, port)
    return new_endpoint.listen(FTPServer())


class FTPClient(ClientFactory):
    protocol = TransferClientProtocol


