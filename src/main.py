import sys
from PySide2.QtWidgets import QApplication
from src.gui import GUI
from src.server import Server
import src.network_discovery as network


if __name__ == '__main__':
    network.bootstrap_local_connections()  # Get all existing shares on the local network or start your own

    # Make this computer act as a master node
    current_port = 3025
    Server(current_port)

    # @TODO only the server or gui runs, not both simultaneously?, not cool
    app = QApplication(sys.argv)
    gui = GUI()
    gui.show()

    sys.exit(app.exec_())








# spawn on 3025 then +1 for each server after that