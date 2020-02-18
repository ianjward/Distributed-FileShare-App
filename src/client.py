from twisted.internet.protocol import Factory, Protocol, ClientFactory
from twisted.internet import reactor


class ClientProtocol(Protocol):
    def dataReceived(self, data):
        print("Data received")


class MyClientFactory(ClientFactory):
    def startedConnecting(self, connector):
        print("Connecting")

    def buildProtocol(self, addr):
        return ClientProtocol()

    def clientConnectionLost(self, connector, reason):
        print(reason)


class Client:
    def __init__(self, port: int, server_ip: str):
        self.port = port
        self.server_ip = server_ip
        reactor.connectTCP(server_ip, port, ClientProtocol())
        reactor.run()