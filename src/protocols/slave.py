from twisted.internet.protocol import Protocol
from src.utilities.messages import decode_msg, Message


class SlaveProtocol(Protocol):
    def connectionMade(self):
        self.factory.new_connection_made(self)

    def dataReceived(self, encoded_msg):
        msg = decode_msg(encoded_msg)
        self.factory.receive_msg(msg, self)

    def clientConnectionLost(self, connector, reason):
        self.factory.connection_lost(self, reason)

    def sendMessage(self, msg: Message):
        encoded_msg = msg.encode_msg()
        self.transport.write(encoded_msg)