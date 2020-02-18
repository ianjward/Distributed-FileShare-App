from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory
from twisted.internet import reactor


class ServerProtocol(LineReceiver):
    def __init__(self):
        self.name = None
        self.master_node = False

    def connectionMade(self):
        if len(self.factory.peers) == 0:
            self.master_node = True
            print("You are the master.")
        self.factory.peers.append(self)
        print("New peer!")

    def connectionLost(self, reason):
        self.factory.peers.remove(self)

    def lineReceived(self, line):
        print("Line received")


class ServerFactory(Factory):
    protocol = ServerProtocol

    def __init__(self):
        self.peers = []
        self.reserved_ports = []


class Server:
    def __init__(self, port: int):
        self.port = port
        print("started server")
        reactor.listenTCP(port, ServerFactory())
        reactor.run()


