import hashlib
import threading
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from src.peer_types.slave_peer import SlaveNode


class ShareFile:
    sha1_hash = hashlib.sha1()
    BUF_SIZE = 262164  # 256kb chunks
    location = 'test.txt'
    chunks = {}

    def __init__(self, file_path:str):
        self.location = file_path

    def __hash__(self):
        index = 0
        # Read in a file 64kb at a time hashing+saving each chunk
        with open(self.location, 'rb') as file:
            while True:
                data = file.read(self.BUF_SIZE)
                if not data:
                    break

                self.sha1_hash.update(data)
                self.chunks[index] = self.sha1_hash
                index += 1
                print("SHA1: {0}".format(self.sha1_hash.hexdigest()))


class FileWatcher(PatternMatchingEventHandler):
    patterns = ['*']

    def __init__(self, share: SlaveNode):
        super().__init__()
        self.share_node = share

    def process(self, event):
        print(event.event_type)
        if event.event_type == 'created':
            self.share_node.file_created(event)

        if event.event_type == 'deleted':
            self.share_node.file_deleted(event)

        if event.event_type == 'modified':
            self.share_node.file_modified(event)

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

    def on_deleted(self, event):
        self.process(event)


def monitor_file_changes(slave:SlaveNode):
    threading.Thread(target=start_file_monitor, args=([slave]), daemon=True).start()


def start_file_monitor(slave:SlaveNode):
    observer = Observer()
    observer.schedule(FileWatcher(slave), 'monitored_files\\')
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()