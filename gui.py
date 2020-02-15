import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver


class GUI(QDialog):
    def __init__(self, parent=None):
        super(GUI, self).__init__(parent)

        # Temp variable for testing
        self.username = "Mass"
        self.port = ""
        self.ip = ""

        # Set Main Window
        self.window = QDialog()

        # Widgets
        self.ip_label = QLabel("Enter IP: ")
        self.port_label = QLabel("Enter Port: ")
        self.ip_line_edit = QLineEdit()
        self.port_line_edit = QLineEdit()
        self.chat_text = QTextEdit()
        self.chat_input = QTextEdit()
        self.join_button = QPushButton("Join Server")
        self.submit_button = QPushButton("Enter")

        # Set placeholders
        self.ip_line_edit.setPlaceholderText("127.0.0.1")
        self.port_line_edit.setPlaceholderText("31337")
        self.chat_text.setPlaceholderText("P2P Chat Service")
        self.chat_input.setPlaceholderText("Enter your message here...")

        # Set layout
        self.layout = QGridLayout()

        # Row 1
        self.row_1 = QHBoxLayout()
        self.row_1.addWidget(self.ip_label)
        self.row_1.addWidget(self.ip_line_edit)
        self.row_1.addWidget(self.port_label)
        self.row_1.addWidget(self.port_line_edit)
        self.row_1.addWidget(self.join_button)

        self.layout.addLayout(self.row_1, 0, 0)
        self.layout.addWidget(self.chat_text, 1, 0)
        self.layout.addWidget(self.chat_input, 2, 0)
        self.layout.addWidget(self.submit_button, 3, 0)

        self.setLayout(self.layout)

        # Button submit clicked method
        self.submit_button.clicked.connect(self.send_message)
        self.join_button.clicked.connect(self.join_server)

    # ==========================
    # Getters
    # ==========================
    def get_ip(self):
        return self.ip

    def get_port(self):
        return self.port

    # ==========================
    # Core Functionality
    # ==========================
    def send_message(self):
        message = self.chat_input.toPlainText()
        self.chat_text.append(f"{self.username}: {message}")
        self.chat_input.clear()
        print(f"Message: {message}")

    def join_server(self):
        self.ip = self.ip_line_edit.text()
        self.port = self.port_line_edit.text()
        print(f"Joining Server\nIP: {self.ip} Port: {self.port}")


class Chat(LineReceiver):

    def __init__(self, users):
        self.users = users
        self.name = None
        self.state = "GETNAME"

    def connectionMade(self):
        self.sendLine(b"What's your name?")

    def connectionLost(self, reason):
        if self.name in self.users:
            del self.users[self.name]

    def lineReceived(self, line):
        if self.state == "GETNAME":
            self.handle_GETNAME(line)
        else:
            self.handle_CHAT(line)

    def handle_GETNAME(self, name):
        if name in self.users:
            self.sendLine(b"Name taken, please choose another.")
            return
        self.sendLine(b"Welcome, %s!" % (name,))
        self.name = name
        self.users[name] = self
        self.state = "CHAT"

    def handle_CHAT(self, message):
        message = "<%s> %s" % (self.name, message)
        for name, protocol in self.users.items():
            if protocol != self:
                protocol.sendLine(message.encode())


class ChatFactory(Factory):

    def __init__(self):
        self.users = {} # maps user names to Chat instances

    def buildProtocol(self, addr):
        return Chat(self.users)


def main():
    app = QApplication(sys.argv)
    import qt5reactor
    qt5reactor.install()

    gui = GUI()
    gui.show()

    from twisted.internet import reactor
    reactor.listenTCP(8123, ChatFactory())
    reactor.run()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()