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
        chunks_needed = file.chunks_needed.split(' ')
        file.file_path = file.get_file_path()
        chunks = self.get_chunks(file.file_path)
        # Return each chunk with its data
        for i in chunks_needed:
            if i != '':
                chunk = Chunk(int(i), file)
                # chunk.data = chunks[int(i)]
                self.callRemote(ReceiveChunk, chunk=chunk.encode())
        return {}
    ServeChunks.responder(serve_chunks)

    def get_chunks(self, file_path:str) -> dict:
        buffer = 60000
        chunks = {}
        index = 0

        with open(file_path, 'rb') as file:
            while True:
                data = file.read(buffer)
                print(data)
                if not data:
                    break
                chunks[index] = data
                index += 1
        print(chunks)
        return chunks


class TransferClientProtocol(AMP):
    def connectionMade(self):
        self.factory.distant_end = self
        print("FTP CLIENT: Connected to server")

    def receive_chunk(self, chunk):
        # global chunks_to_receive
        print('hete')
        # decoded_chunk = chunk.decode_chunk()
        # print("SLAVE: Received chunk", decoded_chunk.index, 'of', decoded_chunk.chunks_in_file, 'for', chunk.file.file_name)
        # file.write_chunk(chunk_index, message['chunk'])
        # Close ftp connection
        # self.chunks_awaiting_update[file.file_name] -= 1
        # self.close_ftp(self.chunks_awaiting_update[file.file_name], file)

        # @TODO close ftp and reset chunks needed
        # deferLater(reactor, 5, self.close_ftp, -1, file)
        return {}
    ReceiveChunk.responder(receive_chunk)


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





