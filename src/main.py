import sys
from PySide2.QtWidgets import QApplication
from src.gui import GUI
from src.server import Server

if __name__ == '__main__':
    current_port = 3025
    Server(current_port)  # 3025 is the port

    # @TODO whichever is launched first (server or gui) is the only thread that runs
    app = QApplication(sys.argv)
    gui = GUI()
    gui.show()

    sys.exit(app.exec_())


# spawn on 3025 then +1 for each server after that