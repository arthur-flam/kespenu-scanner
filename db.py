"""
Utilities to persist the data into a small database...
"""
import zlib
import pickle
import sqlite3

# other options
# - stdlib.shelve
# - https://github.com/dagnelies/pysos
from sqlitedict import SqliteDict

def encode(obj):
    return sqlite3.Binary(zlib.compress(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)))
def decode(obj):
    return pickle.loads(zlib.decompress(bytes(obj)))

def make_db(db_path: str):
    return SqliteDict(db_path, encode=encode, decode=decode)
