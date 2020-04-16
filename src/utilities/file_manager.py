import hashlib
import os
import pickle
import threading
import time
from os.path import abspath
from twisted.internet import defer
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from pathlib import Path
import src.utilities.networking
import sqlite3
from sqlite3 import Error
from peewee import *


cwd = abspath(os.getcwd())
src_path = str(Path(cwd).parents[0])
db_path = os.path.join(src_path, 'files.db')
db = SqliteDatabase(db_path)


def get_local_ip():
    return src.utilities.networking.get_local_ip_address()


class ShareFile:
    sha1_hash = hashlib.sha1()
    BUF_SIZE = 60000  # 60kb chunks to avoid amp limit for v1
    file_path = ''
    chunk_hashes = {}
    addresses = {}
    chunks_needed = ''
    update_index = 0
    update_data = None
    num_chunks = 0

    def __init__(self, file_path: str, share_name: str):
        self.share_name = share_name
        self.file_name = Path(file_path).name
        self.last_mod_time = os.path.getmtime(file_path)
        # db.create_tables([FileData])

        self.__hash__()

    def __hash__(self):
        index = 0
        # Read in a file 60kb at a time hashing+saving each chunk
        with open(self.get_file_path(), 'rb') as file:
            while True:
                data = file.read(self.BUF_SIZE)
                # FileData.create(file_name=self.file_name, chunk_index=index, data=data)
                # print(FileData.get(FileData.chunk_index == index))
                if not data:
                    break

                self.sha1_hash.update(data)
                self.chunk_hashes[index] = self.sha1_hash.hexdigest()
                self.addresses[index] = get_local_ip()
                index += 1
                # print("SHA1: {0}".format(self.sha1_hash.hexdigest()))
        self.num_chunks = index

    def get_chunk(self, chunk_index: int):
        # Seek and return chunk data
        with open(self.file_path, 'rb') as file:
            file.seek(self.BUF_SIZE * chunk_index)
            return file.read(self.BUF_SIZE)

    def encode(self):
        return pickle.dumps(self)

    def get_file_path(self):
        return os.path.join('monitored_files', self.share_name, self.file_name)


class Chunk:
    def __init__(self, index:int, file:ShareFile):
        self.file = file
        self.index = index
        self.data = file.get_chunk(index)
        self.chunks_in_file = file.num_chunks

    def encode(self):
        return pickle.dumps(self)


class FileManager:
    BUF_SIZE = 60000  # 60kb chunks to avoid amp limit for v1
    queue = defer.DeferredQueue()

    def __init__(self):
        print('created file manager')

    def update_file(self, share_file: ShareFile):
        self.queue.put(share_file)
        self.update_queue()

    def update_queue(self):
        share_file = self.queue.get()
        with open(share_file.file_path, 'wb') as file:
            file.seek(self.BUF_SIZE * share_file.update_index)
            # if share_file.

    def write_chunk(self, share_file: ShareFile, chunk_index: int, data):

        # Seek and write chunk data
        with open(share_file.file_path, 'wb') as file:
            file.seek(self.BUF_SIZE * chunk_index)
            file.write(data)

    def get_chunk(self, share_file: ShareFile, chunk_index: int):
        # Seek and return chunk data
        with open(share_file.file_path, 'rb') as file:
            file.seek(self.BUF_SIZE * chunk_index)
            return file.read(self.BUF_SIZE)
# class FileData(Model):
#     file_name = TextField()
#     chunk_index = IntegerField()
#     data = BlobField()
#
#     class Meta:
#         database = db
#         database = db


def decode_file(file:ShareFile):
    return pickle.loads(file)


def decode_chunk(chunk: Chunk):
    return pickle.loads(chunk)


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