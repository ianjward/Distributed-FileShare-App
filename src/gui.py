from PySide2.QtWidgets import QDialog, QLabel, QLineEdit, QTextEdit, QPushButton, QHBoxLayout, \
    QGridLayout


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

    def send_message(self):
        message = self.chat_input.toPlainText()
        self.chat_text.append(f"{self.username}: {message}")
        self.chat_input.clear()
        print(f"Message: {message}")

    def join_server(self):
        self.ip = self.ip_line_edit.text()
        self.port = self.port_line_edit.text()
        print(f"Joining Server\nIP: {self.ip} Port: {self.port}")

