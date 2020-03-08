import sys
from PySide2.QtWidgets import QApplication
from src.gui import GUI
from src.master_node import MasterNode
from src.slave_node import SlaveNode
from twisted.internet import reactor
import src.network_utilities as network


if __name__ == '__main__':
    server_port = 3025
    # local_network = network.find_lan_shares()  # String of IP addresses of every Share gateway on the LAN
    # @TODO Need to wait until shares have been found before this is run
    # share_ips = local_network.available_shares.split(" ")

    # Make this computer act as the master for a share
    MasterNode(server_port, "MyTestShare")

    # Make this computer act as a slave for a share (testing purposes)
    SlaveNode(3025, network.get_local_ip_address())

    # app = QApplication(sys.argv)
    # gui = GUI()
    # gui.show()

    reactor.run()

    # sys.exit(app.exec_())

# spawn on 3025 then +1 for each server after that
