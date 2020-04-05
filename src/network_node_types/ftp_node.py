from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint, connectProtocol
from twisted.internet.protocol import ClientFactory, Factory
from twisted.protocols.amp import AMP
from src.network_traffic_types.ftp_commands import ServeFile
from src.utilities.file_manager import decode_file, ShareFile


class TransferServerProtocol(AMP):
    def connectionMade(self):
        self.factory.distant_end = self
        print("FTP SERVER: Connected to client")

    def serve_file(self, encoded_file, chunks_needed):
        file = decode_file(encoded_file)
        data = file.get_chunks(chunks_needed)
        print('servingfile', file.file_name, chunks_needed)
        file.get_chunks(chunks_needed)
        return {'encoded_file': file}
    ServeFile.responder(serve_file)
# @TODO sever ftp client connection on finish


class TransferClientProtocol(AMP):
    def connectionMade(self):
        self.factory.distant_end = self
        print("FTP CLIENT: Connected to server")


class FTPClient(ClientFactory):
    protocol = TransferClientProtocol
    distant_end = None


class FTPServer(Factory):
    protocol = TransferServerProtocol
    distant_end = None


class FTPClientCreator:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.endpoint = None
        self.factory = FTPClient()

    def start_connect(self):
        self.endpoint = TCP4ClientEndpoint(reactor, self.ip, self.port)
        return self.endpoint.connect(self.factory)


def create_ftp_server(port: int):
    new_endpoint = TCP4ServerEndpoint(reactor, port)
    return new_endpoint.listen(FTPServer())




