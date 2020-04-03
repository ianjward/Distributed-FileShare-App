import hashlib
import os
import pickle
import threading
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class ShareFile:
    sha1_hash = hashlib.sha1()
    BUF_SIZE = 262164  # 256kb chunks
    location = ''
    chunks = {}

    def __init__(self, file_path:str):
        self.location = file_path
        slash_index = file_path.rindex('\\') + 1
        self.file_name = file_path[slash_index:]
        self.last_mod_time = os.path.getmtime(file_path)
        self.__hash__()

    def __hash__(self):
        index = 0
        # Read in a file 64kb at a time hashing+saving each chunk
        with open(self.location, 'rb') as file:
            while True:
                data = file.read(self.BUF_SIZE)
                if not data:
                    break

                self.sha1_hash.update(data)
                self.chunks[index] = self.sha1_hash.hexdigest()
                index += 1
                # print("SHA1: {0}".format(self.sha1_hash.hexdigest()))

    def encode(self):
        return pickle.dumps(self)


def decode_file(file:ShareFile):
    return pickle.loads(file)


class FileWatcher(PatternMatchingEventHandler):
    patterns = ['*']

    def __init__(self, share):
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


def monitor_file_changes(slave):
    threading.Thread(target=start_file_monitor, args=([slave]), daemon=True).start()


def start_file_monitor(slave):
    observer = Observer()
    observer.schedule(FileWatcher(slave), 'monitored_files\\' + slave.share_name + '\\')
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


# def create_file(self):
#     file = open("test.txt", "w+")
#     file.write("hello world")
#     file.close()