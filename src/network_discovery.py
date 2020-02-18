# Handles the initial network discovery for now
from _socket import SOL_SOCKET, SO_BROADCAST
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor


# Broadcasts all of the master node ip's so a new computer knows what shares are on the network
class SendMasterAddresses(DatagramProtocol):
    def __init__(self):
        self.available_shares = "192.168.1.106"  # Should be a list or something later on

    def datagramReceived(self, datagram, address):
        print("Received request from: " + str(address))
        self.transport.write(str.encode(self.available_shares), address)


# Sends a broadcast over local network to get all master node ip's, only master nodes respond as they are the only ones
# who are aware of the other master nodes
class GetMasterAddresses(DatagramProtocol):
    def startProtocol(self):
        self.transport.socket.setsockopt(SOL_SOCKET, SO_BROADCAST, True)
        self.sendDatagram()
        self.number_of_requests = 0

    def sendDatagram(self):
        datagram = str.encode("Requests master node ip's")
        self.transport.write(datagram, ('255.255.255.255', 7999))

    def datagramReceived(self, datagram, host):
        self.number_of_requests += 1
        print('Datagram received: ', repr(datagram))
        # if self.number_of_requests == 1:
        #     reactor.stop()


# Broadcasts master ip's
def broadcast_master_addresses():
    print("Listening for master address broadcast requests")
    reactor.listenUDP(7999, SendMasterAddresses())
    reactor.run()


# Requests master node ip's
def request_master_addresses():
    reactor.listenUDP(7999, GetMasterAddresses())
    reactor.run()


# Will eventually attempt to get all master nodes on the network, if there are none, makes itself a master
def bootstrap_local_connections():
    # @TODO attempt to get master node addresses with src.request_master_addresses, timeout after 5s or and become master

    # @TODO Put this broadcast in an async thread so it doesn't interfere with file transfer/GUI activities.
    broadcast_master_addresses()