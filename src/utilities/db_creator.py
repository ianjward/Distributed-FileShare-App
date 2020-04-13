import os
import sqlite3
from sqlite3 import Error
from os.path import abspath
from pathlib import Path
from peewee import *


cwd = abspath(os.getcwd())
src_path = str(Path(cwd).parents[0])
db_path = os.path.join(src_path, 'files.db')
db = SqliteDatabase(db_path)


class FileData(Model):
    file_name = TextField()
    chunk_index = IntegerField()
    data = BlobField()

    class Meta:
        database = db


def create_connection():
    cwd = abspath(os.getcwd())
    src_path = str(Path(cwd).parents[0])
    db_path = os.path.join(src_path, 'files.db')

    connection = None
    try:
        connection = sqlite3.connect(db_path)

        print(sqlite3.version)
    except Error as e:
        print(e)
    return connection


def clear_all_db_files():
    for file in FileData.select():
        file.delete_instance()
        print('Deleted', file.file_name)


def print_db_entries():
    for file in FileData.select():
        print(file.file_name)

# grandma = Person.get(Person.name == 'Grandma L.')
# for person in Person.select().order_by(Person.birthday.desc()):


if __name__ == '__main__':
    # db.create_tables([FileData])
    db.drop_tables([FileData])
    # try:
    #     newFile = FileData.create(file_name='file1', chunk_index=0, data=b'aaaa')
    #     newFile2 = FileData.create(file_name='file2', chunk_index=1, data=b'ffff')
    # except (IntegrityError, Error) as e:
    #     print(e)
    print(db.get_tables())
    print_db_entries()

    # clear_all_db_files()

    # create_connection()

