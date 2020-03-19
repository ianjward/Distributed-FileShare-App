import socket
from src.utilities.files import ShareFile, monitor_file_changes
from src.peer_types.master_peer import MasterNode
from src.peer_types.slave_peer import SlaveNode
from twisted.internet import reactor


# Returns internet facing IP. Might not work without internet? But works on both linux and Windows while others did not.
def get_local_ip_address():
    internet = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    internet.connect(("8.8.8.8", 80))
    return internet.getsockname()[0]


if __name__ == '__main__':
    server_port = 3025

    MasterNode(server_port, "MyTestShare", '1234')
    share_slave = SlaveNode(3025, get_local_ip_address())


    # @TODO Need to wait until shares have been found before this is run
    # share_ips = local_network.available_shares.split(" ")

    # Make this computer act as the master for a share
    # MasterNode(server_port, "MyTestShare", '1234')

    # Make this computer act as a slave for a share (testing purposes)
    # share_slave = SlaveNode(3025, network.get_local_ip_address())
    #
    # share_file = ShareFile('monitored_files/test.txt')
    # share_file.__hash__()
    # monitor_file_changes(share_slave)
    # app = QApplication(sys.argv)
    # gui = GUI()
    # gui.show()
    reactor.run()

    # sys.exit(app.exec_())
# spawn on 3025 then +1 for each server after that


# pywin32==227
