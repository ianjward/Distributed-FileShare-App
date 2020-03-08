from twisted.internet import reactor
from src.protocols import SlaveFactory


class SlaveNode:
    def __init__(self, port: int, server_ip: str):
        protocol_factory = SlaveFactory(server_ip)
        reactor.connectTCP(server_ip, port, protocol_factory)
        reactor.run()


