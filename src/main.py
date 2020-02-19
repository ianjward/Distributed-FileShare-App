import sys
from PySide2.QtWidgets import QApplication
from src.gui import GUI
from src.share_controller import ShareController
from src.share_member import ShareMember
from twisted.internet import reactor
import src.network_discovery as network


if __name__ == '__main__':
    server_port = 3025
    # local_network = network.find_local_shares()  # String of IP addresses of every Share gateway on the LAN

    # @TODO Need to wait until shares have been found before this is run
    # share_ips = local_network.available_shares.split(" ")

    # Make this computer act as the gateway to a share
    ShareController(server_port, "MyTestShare", "192.168.1.106")
    ShareMember(3025, "192.168.1.106")

    # app = QApplication(sys.argv)
    # gui = GUI()
    # gui.show()

    reactor.run()

    # sys.exit(app.exec_())

# spawn on 3025 then +1 for each server after that
