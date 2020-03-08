from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from src.protocols import MasterFactory
from src.network_utilities import get_local_ip_address


class MasterNode:
    def __init__(self, port: int, share_name: str):
        protocol_factory = MasterFactory(share_name, "1234")

        print("MASTER: Started a share on ", get_local_ip_address(),":", port)
        server_end_point = TCP4ServerEndpoint(reactor, port)
        server_end_point.listen(protocol_factory)





