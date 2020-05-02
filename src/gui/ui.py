import os
import threading
import time
from functools import partial
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QFileSystemModel, QTreeView, QTextEdit, QShortcut, QLabel, QMessageBox, QWidget
from PyQt5.QtWidgets import QPushButton
from pathlib import Path
import shutil
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from watchdog.events import FileCreatedEvent, FileDeletedEvent


class Ui_MainWindow(object):
    opening_file = True
    row = 0
    column = 0

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 749)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setTabShape(QtWidgets.QTabWidget.Rounded)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        self.centralwidget.setFont(font)
        self.centralwidget.setObjectName("centralwidget")

        self.horizontalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(10, 10, 1261, 711))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.user_interface = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.user_interface.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.user_interface.setContentsMargins(0, 0, 0, 0)
        self.user_interface.setObjectName("user_interface")

        self.file_tree = QtWidgets.QTreeView(self.horizontalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.file_tree.sizePolicy().hasHeightForWidth())
        self.file_tree.setSizePolicy(sizePolicy)
        self.file_tree.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.file_tree.setObjectName("file_tree")
        self.user_interface.addWidget(self.file_tree)

        self.share_tabs = QtWidgets.QTabWidget(self.horizontalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        # sizePolicy.setHeightForWidth(self.share_tabs.sizePolicy().hasHeightForWidth())
        self.share_tabs.setSizePolicy(sizePolicy)
        self.share_tabs.setObjectName("share_tabs")

        self.ians_share_tab = QtWidgets.QWidget()
        self.ians_share_tab.setObjectName("ians_share_tab")
        self.grid_layout = QtWidgets.QWidget(self.ians_share_tab)
        self.grid_layout.setGeometry(QtCore.QRect(-1, -1, 631, 681))
        self.grid_layout.setObjectName("grid_layout")

        self.ians_share_grid = QtWidgets.QGridLayout(self.grid_layout)
        self.ians_share_grid.setColumnStretch(0, 4)
        self.ians_share_grid.setColumnStretch(1, 4)
        self.ians_share_grid.setColumnStretch(2, 4)
        self.ians_share_grid.setColumnStretch(3, 4)
        self.ians_share_grid.setContentsMargins(10, 15, 15, 15)
        self.ians_share_grid.setObjectName("ians_share_grid")
        self.share_tabs.addTab(self.ians_share_tab, "")


        self.new_share_tab = QtWidgets.QWidget()
        self.new_share_tab.setObjectName("new_share_tab")
        self.share_tabs.addTab(self.new_share_tab, "")

        self.user_interface.addWidget(self.share_tabs)
        self.user_interface.setStretch(0, 1)
        self.user_interface.setStretch(1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        # Setup Gui Contents and Listeners
        self.create_file_tree()
        self.load_existing_files()
        self.file_tree.doubleClicked.connect(self.tree_item_clicked)

        monitor_file_changes(self)
        self.retranslate_ui(MainWindow)
        self.share_tabs.setCurrentIndex(0)
        self.current_file = ''
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslate_ui(self, main_window):
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("MainWindow", "Spencer and Ian\'s Distributed Fileshare"))
        self.share_tabs.setTabText(self.share_tabs.indexOf(self.ians_share_tab), _translate("MainWindow", "Ians Share"))
        self.share_tabs.setTabText(self.share_tabs.indexOf(self.new_share_tab), _translate("MainWindow", "+"))

    def create_file_tree(self):
        os_root = os.path.abspath(os.sep)
        self.model = QFileSystemModel()
        self.model.setRootPath(os_root)
        self.file_tree.setModel(self.model)

        self.file_tree.expandToDepth(1)
        self.file_tree.resizeColumnToContents(0)
        self.file_tree.setAnimated(False)
        self.file_tree.setIndentation(20)
        self.file_tree.setSortingEnabled(True)

    def tree_item_clicked(self, index):
        self.current_file = self.model.filePath(index)
        file_name = self.current_file[self.current_file.rfind('/') + 1:]

        # Avoid adding duplicate files
        if file_name in os.listdir(self.share_loc()):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)

            msg.setText("Duplicate Names Not Allowed in Share")
            msg.setWindowTitle("File Not Shared")
            msg.setDetailedText("To add a file ensure that the file name is not already in use. Differences in case do not differentiate names.")
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
        else:
            self.create_share_button(file_name)

    def file_created(self, event: FileCreatedEvent):
        # stub not currently needed
        a = 1
        # print(event.src_path, event.event_type)

    def toggle_opening(self):
        self.opening_file = not self.opening_file
        print('')

    def file_deleted(self, event: FileDeletedEvent):
        # Remove button from share display
        try:
            button_name = Path(event.src_path).name
            button = self.ians_share_tab.findChild(QPushButton, button_name)
            button.deleteLater()
            os.remove(event.src_path)
        except:
            print(event.src_path, 'removed')

    def manual_delete(self, button_name: str):
        path = os.path.join(self.share_loc(), button_name)
        button = self.ians_share_tab.findChild(QPushButton, button_name)
        button.deleteLater()
        os.remove(path)

    def load_existing_files(self):
        os.chdir('../../..')

        # Create button for each file
        for file in os.listdir(self.share_loc()):
            self.current_file = os.path.join(self.share_loc(),file)
            self.create_share_button(Path(file).name)

    def create_share_button(self, name:str):
        try:
            shutil.copy2(self.current_file, self.share_loc())
        except shutil.SameFileError as e:
            print('Avoiding duplicate copy of ', e)

        button = QPushButton(name)
        button.setObjectName(name)

        self.ians_share_grid.addWidget(button, self.row,self.column, QtCore.Qt.AlignTop)
        self.column += 1
        if self.column == 4:
            self.column = 0
            self.row += 1

        new_file = os.path.join(self.share_loc(), name)
        button.clicked.connect(partial(self.open_file, new_file))  # Interesting: if using a lambda instead of a partial gc doesn't occur so same file is always loaded

    def open_file(self, path:str):
        modifiers = QtWidgets.QApplication.keyboardModifiers()

        # Hold ctrl and click on a file to delete
        if modifiers == QtCore.Qt.ControlModifier:
            self.manual_delete(Path(path).name)
        else:
            try:
                os.startfile(path, 'open')
            except:
                print('File can\'t be opened!')

    def share_loc(self):
        return os.path.join(os.path.abspath(os.curdir),'Distributed-FileShare-App', 'src', 'monitored_files', 'ians_share')


class FileWatcher(PatternMatchingEventHandler):
    patterns = ['*']

    def __init__(self, gui):
        super().__init__()
        self.subscriber = gui

    def process(self, event):
        if event.event_type == 'created':
            self.subscriber.file_created(event)

        if event.event_type == 'deleted':
            self.subscriber.file_deleted(event)

    def on_created(self, event):
        self.process(event)

    def on_deleted(self, event):
        self.process(event)


def monitor_file_changes(gui):
    threading.Thread(target=start_file_monitor, args=([gui]), daemon=True).start()


def start_file_monitor(gui):
    observer = Observer()
    observer.schedule(FileWatcher(gui), gui.share_loc())
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

