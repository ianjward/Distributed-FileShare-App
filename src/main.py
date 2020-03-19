from src.utilities.files import ShareFile, monitor_file_changes
from src.peer_types.master_peer import MasterNode
from src.peer_types.slave_peer import SlaveNode
from twisted.internet import reactor
import src.utilities.networking as network


if __name__ == '__main__':
    server_port = 3025

    # MasterNode(server_port, "MyTestShare", '1234')
    # share_slave = SlaveNode(3025, '192.168.1.105')


    # @TODO Need to wait until shares have been found before this is run
    master_ips_string = network.find_lan_shares()
    master_ips = master_ips_string.split(" ")
    print(master_ips)
    # Make this computer act as the master for a share
    MasterNode(server_port, "MyTestShare", '1234')

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
