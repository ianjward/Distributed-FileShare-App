from twisted.internet import reactor
import src.utilities.protocols as network


if __name__ == '__main__':
    # share_slave = SlaveNode(3025, '192.168.1.105')
    network.find_lan_shares()
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
