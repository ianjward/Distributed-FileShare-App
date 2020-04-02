import netifaces as netifaces
from _socket import SOL_SOCKET, SO_BROADCAST
from twisted.internet.protocol import DatagramProtocol
from twisted.protocols.policies import TimeoutMixin
from src.network_node_types.master_node import MasterNode
from src.network_node_types.slave_node import SlaveNode
from src.network_traffic_types.messages import *
from twisted.application import internet
from twisted.internet import reactor


class BroadcastNode(DatagramProtocol, TimeoutMixin):
    wanted_networks = []

    def startProtocol(self):
        self.transport.socket.setsockopt(SOL_SOCKET, SO_BROADCAST, True)
        self.state = "NEEDS_IPS"
        self.available_shares = {}
        self.send_datagram(RequestMastersMsg())
        reactor.callLater(3.5, self.create_network_node)

    def send_datagram(self, msg:Message):
        broadcast_port = 7999
        broadcast_ip = '255.255.255.255'
        self.transport.write(msg.encode_msg(), (broadcast_ip, broadcast_port))

    def datagramReceived(self, encoded_msg, host: tuple):
        msg = decode_msg(encoded_msg)
        sender = host[0]
        valid_sender = self.sender_is_valid(sender)
        mtype = msg.mType

        if mtype == 'REQST_MSTRS' and valid_sender:
            print("BROADCAST: Received msg", msg.mType)
            self.send_master_list(sender)

        elif mtype == 'MSTR_LIST' and valid_sender:
            print("BROADCAST: Received msg", msg.mType)
            self.receive_master_list(msg)

        elif mtype == 'MSTR_UPDTE':
            print("BROADCAST: Received msg", msg.mType)
            self.receive_master_list(msg)

    def send_master_list(self, sender:tuple):
        if self.state == "HAS_IPS":
            response = MasterListMsg(self.available_shares).encode_msg()
            self.transport.write(response, (sender, 7999))
            print("BROADCAST: Received Share ip request from: " + str(sender))
            print("BROADCAST: Responded to ", str(sender), " with ", self.available_shares)

    def receive_master_list(self, msg:MasterListMsg):
        self.available_shares = msg.master_dict
        print('BROADCAST: Dictionary set:', msg.master_dict)
        self.state = "HAS_IPS"

    def join_network_as_slave(self, share_name, available_shares):
        # @TODO bump up Master port by 1, have master open new port, and send dictionary update on broadcast
        # global wanted_networks
        if share_name in self.wanted_networks:
            port = available_shares[share_name][0]
            master_ip = available_shares[share_name][1]
            SlaveNode(port, master_ip, share_name)

    def create_network_node(self):
        if self.state == 'NEEDS_IPS':
            self.state = "HAS_IPS"
            self.available_shares["ians_share"] = (3025, self.get_local_ip())
            print("BROADCAST: No available shares found.")
            MasterNode(3025, "ians_share", '1234', self)
            # @TODO read-in share name + access code + always just start at 3025?

        for share in self.available_shares:
            self.join_network_as_slave(share, self.available_shares)

    def get_local_ip(self):
        return src.utilities.networking.get_local_ip_address()

    # Ensures sender isn't the local host
    def sender_is_valid(self,sender: str) -> bool:
        self_ips = []

        # Gets computer's local network interfaces and puts them in a list
        for interface in netifaces.interfaces():
            interface_details = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in interface_details:
                verbose_address = interface_details[netifaces.AF_INET]
                self_ips.append(verbose_address[0]["addr"])

        # Sender is invalid if it is a local ip interface
        if sender in self_ips:
            return False
        return True


# Discovers all available shares on the lan
def search_for(share_names:list):
    print("BROADCAST: Searching for Lan Shares")
    BroadcastNode.wanted_networks = share_names

    discovery_protocol = BroadcastNode()
    server = internet.UDPServer(7999, discovery_protocol)
    server.startService()