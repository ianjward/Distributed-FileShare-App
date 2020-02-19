from time import strftime

from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory
from twisted.internet import reactor, protocol
import uuid
from datetime import date, datetime, time


class ShareControllerProtocol(LineReceiver):
    def connectionMade(self):
        print("CONTROLLER: New connection detected!")
        self.sendLine(str.encode("AUTHENTICATE"))

    def connectionLost(self, reason):
        self.factory.nodes.remove(self)

    def dataReceived(self, data):
        message = data.decode("ascii").split(" ")
        if message[0] == "AUTH_SYN":
            self.authenticate(message)

    def sendLine(self, line):
        self.transport.write(line)
        print("CONTROLLER: sending", repr(line))

    # message [Authentication, ip, accesscode, username, password]
    def authenticate(self, message):
        if message[2] == self.factory.access_code:
            self.factory.nodes.append(message[1])
            print("CONTROLLER: Authenticated: ", message[1], message[3], message[4])


class ShareControllerFactory(Factory):
    protocol = ShareControllerProtocol

    def __init__(self, share_name:str, access_code: str, ip:str):
        self.nodes = []
        self.users = []
        self.files = []
        self.name = share_name
        self.uuid = share_name + "_" + datetime.now().strftime("%Y-%m-%d-%H:%M:%S") + "_" + str(uuid.getnode())
        self.access_code = access_code
        self.ip = ip


class ShareController:
    def __init__(self, port: int, share_name: str, ip: str):
        controller_factory = ShareControllerFactory(share_name, "1234", ip)

        print("CONTROLLER: Started a share on ", ip,":", port)
        server_end_point = TCP4ServerEndpoint(reactor, port)
        server_end_point.listen(controller_factory)





