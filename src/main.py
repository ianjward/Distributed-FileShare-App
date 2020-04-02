from twisted.internet import reactor
import src.network_node_types.broadcast_node as broadcast

if __name__ == '__main__':
    broadcast.search_for(["ians_share"])
    # app = QApplication(sys.argv)
    # gui = GUI()
    # gui.show()
    reactor.run()

    # sys.exit(app.exec_())


# pywin32==227
