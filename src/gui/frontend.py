import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from ui import Ui_MainWindow, start_file_monitor


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.show()


app = QApplication([])
style_sheet="style2.qss"
with open(style_sheet,"r") as file:
    app.setStyleSheet(file.read())
window = AppWindow()
window.show()
sys.exit(app.exec_())
