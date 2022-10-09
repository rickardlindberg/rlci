import builtins
import os
import tempfile

class Filesystem:

    """
    I can read and write files.

    >>> filesystem = Filesystem.create()
    >>> tmp_dir = tempfile.TemporaryDirectory()
    >>> tmp_path = os.path.join(tmp_dir.name, "tmp.txt")
    >>> filesystem.write(tmp_path, "hello")
    >>> filesystem.read(tmp_path)
    'hello'
    >>> os.path.exists(tmp_path)
    True

    The in memory version of me does not touch the filesystem:

    >>> filesystem = Filesystem.create_in_memory()
    >>> tmp_dir = tempfile.TemporaryDirectory()
    >>> tmp_path = os.path.join(tmp_dir.name, "tmp.txt")
    >>> filesystem.write(tmp_path, "hello")
    >>> filesystem.read(tmp_path)
    'hello'
    >>> os.path.exists(tmp_path)
    False
    """

    def __init__(self, builtins):
        self.builtins = builtins

    def write(self, path, contents):
        with self.builtins.open(path, "w") as f:
            f.write(contents)

    def read(self, path):
        with self.builtins.open(path, "r") as f:
            return f.read()

    @staticmethod
    def create():
        return Filesystem(builtins=builtins)

    @staticmethod
    def create_in_memory():
        store = {}
        class File:
            def __init__(self, path):
                self.path = path
            def __enter__(self):
                return self
            def __exit__(self, type, value, traceback):
                pass
        class FileRead(File):
            def read(self):
                return store[self.path]
        class FileWrite(File):
            def write(self, contents):
                store[self.path] = contents
        class InMemoryOpen:
            def open(self, path, mode):
                if mode == "r":
                    return FileRead(path)
                elif mode == "w":
                    return FileWrite(path)
        return Filesystem(builtins=InMemoryOpen())

