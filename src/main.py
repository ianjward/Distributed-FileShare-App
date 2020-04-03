from twisted.internet import reactor
import src.network_node_types.broadcast_node as broadcast
from src.network_node_types.slave_node import SlaveNode

if __name__ == '__main__':
    broadcast.search_for(["ians_share"])
    # SlaveNode(3026, "192.168.1.106", 'ian\'s_share')

    # app = QApplication(sys.argv)
    # gui = GUI()
    # gui.show()
    reactor.run()

    # sys.exit(app.exec_())


# pywin32==227
