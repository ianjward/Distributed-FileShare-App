from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint, connectProtocol
from twisted.internet.protocol import ClientFactory, Factory
from twisted.protocols.amp import AMP
from src.utilities.file_manager import Chunk
from src.network_traffic_types.ftp_cmds import ServeChunks, ReceiveChunk
from src.utilities.file_manager import decode_file, ShareFile


class TransferServerProtocol(AMP):

    def connectionMade(self):
        self.factory.distant_end = self
        print("FTP SERVER: Connected to client")

    def serve_chunks(self, encoded_file, sender_ip):
        file = decode_file(encoded_file)
        print('FTP SERVER: Serving file', file.file_name)
        for i in file.chunks_needed:
            Chunk(i, file).encode()
            self.callRemote(ReceiveChunk, Chunk(i, file).encode())
        return {}
    ServeChunks.responder(serve_chunks)
# @TODO sever ftp client connection on finish? or did i do this earlier in slave?


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





