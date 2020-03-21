from twisted.internet.protocol import Protocol
from src.utilities.messages import decode_msg, Message


class MasterProtocol(Protocol):
    def connectionMade(self):
        self.factory.new_connection_made(self)

    def connectionLost(self, reason):
        self.factory.connection_lost(self, reason)

    def dataReceived(self, encoded_msg):
        msg = decode_msg(encoded_msg)
        self.factory.receive_msg(msg, self)

    def sendMessage(self, msg:Message):
        encoded_msg = msg.encode_msg()
        self.transport.write(encoded_msg)