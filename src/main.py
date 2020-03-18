from src.utilities.file_utilities import ShareFile, monitor_file_changes
from src.peer_types.master_peer import MasterNode
from src.peer_types.slave_peer import SlaveNode
from twisted.internet import reactor
import src.utilities.network_utilities as network


if __name__ == '__main__':
    server_port = 3025
    # local_network = network.find_lan_shares()  # String of IP addresses of every Share gateway on the LAN
    # @TODO Need to wait until shares have been found before this is run
    # share_ips = local_network.available_shares.split(" ")

    # Make this computer act as the master for a share
    MasterNode(server_port, "MyTestShare", '1234')

    # Make this computer act as a slave for a share (testing purposes)
    share_slave = SlaveNode(3025, network.get_local_ip_address())

    share_file = ShareFile('monitored_files/test.txt')
    share_file.__hash__()
    monitor_file_changes(share_slave)
    # app = QApplication(sys.argv)
    # gui = GUI()
    # gui.show()

    reactor.run()
    # sys.exit(app.exec_())

# spawn on 3025 then +1 for each server after that
