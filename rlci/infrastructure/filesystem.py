import builtins
import contextlib
import os
import tempfile

from rlci.events import Observable, Events

class Filesystem(Observable):

    """
    I am an infrastructure wrapper for filesystem operations.

    Writing files
    =============

    >>> filesystem = Filesystem.create()
    >>> events = Events.capture_from(filesystem)

    When I write a file like this:

    >>> tmp_dir = tempfile.TemporaryDirectory()
    >>> tmp_path = os.path.join(tmp_dir.name, "tmp.txt")
    >>> filesystem.write(tmp_path, "hello")

    The file is written to disk:

    >>> with open(tmp_path) as f:
    ...    f.read()
    'hello'

    You can observe that I wrote the file to disk:

    >>> events # doctest: +ELLIPSIS
    WRITE_FILE =>
        contents: 'hello'
        path: '.../tmp.txt'

    The null version of me does not actually write files to disk:

    >>> tmp_dir = tempfile.TemporaryDirectory()
    >>> tmp_path = os.path.join(tmp_dir.name, "tmp.txt")
    >>> Filesystem.create_null().write(tmp_path, "hello")
    >>> os.path.exists(tmp_path)
    False
    """

    @staticmethod
    def create():
        return Filesystem(builtins=builtins)

    @staticmethod
    def create_null():
        class NullFile:
            def write(self, data):
                pass
        class NullBuiltins:
            @contextlib.contextmanager
            def open(self, path, mode):
                yield NullFile()
        return Filesystem(builtins=NullBuiltins())

    def __init__(self, builtins):
        Observable.__init__(self)
        self.builtins = builtins

    def write(self, path, contents):
        with self.builtins.open(path, "w") as f:
            f.write(contents)
        self.notify("WRITE_FILE", {"path": path, "contents": contents})
