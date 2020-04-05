import hashlib
import os
import pickle
import threading
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from pathlib import Path
import src.utilities.networking


def get_local_ip():
    return src.utilities.networking.get_local_ip_address()


class ShareFile:
    sha1_hash = hashlib.sha1()
    # BUF_SIZE = 262164  # 256kb chunks
    BUF_SIZE = 60000  # 60kb chunks to avoid amp limit for v1
    file_path = ''
    hash_chunks = {}
    addresses = {}

    def __init__(self, file_path: str, share_name: str):
        # self.file_path = file_path
        self.share_name = share_name
        self.file_name = Path(file_path).name
        self.last_mod_time = os.path.getmtime(file_path)
        self.__hash__()

    def __hash__(self):
        index = 0
        # Read in a file 60kb at a time hashing+saving each chunk
        with open(self.get_file_path(), 'rb') as file:
            while True:
                data = file.read(self.BUF_SIZE)
                if not data:
                    break

                self.sha1_hash.update(data)
                self.hash_chunks[index] = self.sha1_hash.hexdigest()
                self.addresses[index] = get_local_ip()
                index += 1
                # print("SHA1: {0}".format(self.sha1_hash.hexdigest()))

    def encode(self):
        return pickle.dumps(self)

    def get_chunk(self, chunk_index):
        # Seek and return chunk data
        with open(self.get_file_path(), 'rb') as file:
            file.seek(self.BUF_SIZE * chunk_index)
            return file.read(self.BUF_SIZE)

    def get_file_path(self):
        return os.path.join('monitored_files', self.share_name, self.file_name)


def decode_file(file:ShareFile):
    return pickle.loads(file)


class FileWatcher(PatternMatchingEventHandler):
    patterns = ['*']

    def __init__(self, share):
        super().__init__()
        self.share_node = share

    def process(self, event):
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
    path_to_files = os.path.join('monitored_files', slave.share_name)
    observer.schedule(FileWatcher(slave), path_to_files)
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