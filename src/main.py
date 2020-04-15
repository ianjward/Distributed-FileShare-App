from twisted.internet import reactor
from PyQt5.QtWidgets import QApplication
import src.network_node_types.broadcast_node as broadcast
import sys
from src.gui.main_window import GUI
import qt5reactor
from src.network_node_types.slave_node import SlaveNode


if __name__ == '__main__':
    # broadcast.search_for(["ians_share"])
    # SlaveNode(3026, "192.168.1.106", 'ian\'s_share')
    app = QApplication(sys.argv)

    qt5reactor.install()

    gui = GUI(reactor)
    gui.show()
    reactor.run()

    sys.exit(app.exec_())


# pywin32==227
