from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint, connectProtocol
from twisted.internet.protocol import ClientFactory, Factory
from twisted.protocols.amp import AMP

import src
from src.utilities.file_manager import Chunk, decode_chunk
from src.network_traffic_types.ftp_cmds import ServeChunks, ReceiveChunk, InitiateServe, ClientServeChunks, \
    ClientReceiveChunk
from src.utilities.file_manager import decode_file, ShareFile


class TransferServerProtocol(AMP):

    def connectionMade(self):
        self.factory.distant_end = self
        print("FTP SERVER: Connected to client")

    def initiate_serve(self, encoded_file):
        file = decode_file(encoded_file)
        self.callRemote(ClientServeChunks, encoded_file=file.encode(), sender_ip=get_local_ip())
        return {}
    InitiateServe.responder(initiate_serve)

    def serve_chunks(self, encoded_file, sender_ip):
        file = decode_file(encoded_file)
        print('FTP SERVER:', get_local_ip(), 'Serving file', file.file_name)
        chunks_needed = file.chunks_needed.split(' ')
        file.file_path = file.get_file_path()
        chunks = self.get_chunks(file.file_path)
        # Return each chunk with its data
        for i in chunks_needed:
            if i != '':
                chunk = Chunk(int(i), file)
                chunk.data = chunks[int(i)]
                self.callRemote(ReceiveChunk, chunk=chunk.encode())
        return {}
    ServeChunks.responder(serve_chunks)

    def get_chunks(self, file_path: str) -> dict:
        buffer = 60000
        chunks = {}
        index = 0

        with open(file_path, 'rb') as file:
            while True:
                data = file.read(buffer)
                if not data:
                    break
                chunks[index] = data
                index += 1
        return chunks


class TransferClientProtocol(AMP):
    def connectionMade(self):
        self.factory.distant_end = self
        print("FTP CLIENT: Connected to server")

    def receive_chunk(self, chunk):
        decoded_chunk = decode_chunk(chunk)
        print("FTP CLIENT: Received chunk",
              decoded_chunk.index + 1, 'of', decoded_chunk.chunks_in_file, 'for',
              decoded_chunk.file.file_name, 'Data:', decoded_chunk.data)
        self.factory.slave.receive_chunk(decoded_chunk)
        return {}
    ClientReceiveChunk.responder(receive_chunk)

    def serve_chunks(self, encoded_file, sender_ip):
        file = decode_file(encoded_file)
        print('FTP SERVER: Serving file', file.file_name)
        chunks_needed = file.chunks_needed.split(' ')
        file.file_path = file.get_file_path()
        chunks = self.get_chunks(file.file_path)
        # Return each chunk with its data
        for i in chunks_needed:
            if i != '':
                chunk = Chunk(int(i), file)
                chunk.data = chunks[int(i)]
                self.callRemote(ReceiveChunk, chunk=chunk.encode())
        return {}
    ClientServeChunks.responder(serve_chunks)

    def get_chunks(self, file_path: str) -> dict:
        buffer = 60000
        chunks = {}
        index = 0

        with open(file_path, 'rb') as file:
            while True:
                data = file.read(buffer)
                if not data:
                    break
                chunks[index] = data
                index += 1
        return chunks


class FTPClient(ClientFactory):
    protocol = TransferClientProtocol
    distant_end = None
    slave = None


class FTPServer(Factory):
    protocol = TransferServerProtocol
    distant_end = None


class FTPClientCreator:
    def __init__(self, ip: str, port: int, slave):
        self.ip = ip
        self.port = port
        self.endpoint = None
        self.factory = FTPClient()
        self.factory.slave = slave

    def start_connect(self):
        self.endpoint = TCP4ClientEndpoint(reactor, self.ip, self.port)
        return self.endpoint.connect(self.factory)


def create_ftp_server(port: int):
    new_endpoint = TCP4ServerEndpoint(reactor, port)
    return new_endpoint.listen(FTPServer())


def get_local_ip():
    return src.utilities.networking.get_local_ip_address()


