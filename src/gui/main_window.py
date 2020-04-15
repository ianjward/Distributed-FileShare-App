import sys
from PyQt5.QtWidgets import QMainWindow


class GUI(QMainWindow):
    def __init__(self, reactor, parent=None):
        super(GUI, self).__init__(parent)
        self.reactor = reactor
        self.resize(250,150)
        self.move(300,300)
        self.setWindowTitle('Simple')

    def closeEvent(self, e):
        self.reactor.stop()