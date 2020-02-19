from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory
from twisted.internet import reactor, protocol


class GatewayProtocol(LineReceiver):
    def __init__(self):
        self.name = None
        self.master_node = False

    def connectionMade(self):
        if len(self.factory.peers) == 0:
            self.master_node = True
            print("You are a gateway.")
        self.factory.peers.append(self)
        print("New peer!")

    def connectionLost(self, reason):
        self.factory.peers.remove(self)

    def lineReceived(self, line):
        print("Line received")


class GatewayFactory(Factory):
    protocol = GatewayProtocol

    def __init__(self):
        self.peers = []
        self.reserved_ports = []


class ShareGateway:
    def __init__(self, port: int):
        self.port = port
        print("Started a share gateway on ", port)
        server_end_point = TCP4ServerEndpoint(reactor, port)
        server_end_point.listen(GatewayFactory())





