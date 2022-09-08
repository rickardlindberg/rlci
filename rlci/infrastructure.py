import builtins
import os
import socket
import subprocess
import sys
import tempfile
import time

from rlci.events import Observable, Events

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

class Process(Observable):

    """
    I am an infrastructure wrapper for running processes.

    I run a process and return its exit code:

    >>> Process.create().run(["python3", "-c", "import sys; sys.exit(99)"])
    99

    I stream output:

    >>> output = []
    >>> _ = Process.create().run(
    ...     ["python", "-c", "import sys; sys.stdout.write('one\\\\n'); sys.stdout.flush(); sys.stderr.write('two\\\\n')"],
    ...     output=output.append
    ... )
    >>> output
    ['one', 'two']

    I log the process I run:

    >>> events = Events()
    >>> _ = events.listen(Process.create_null()).run(["echo", "hello"])
    >>> events
    PROCESS => ['echo', 'hello']

    The null version of me does not run any process:

    >>> Process.create_null().run(["python3", "-c", "import sys; sys.exit(99)"])
    0

    The null version of me can configure responses:

    >>> process = Process.create_null(responses=[
    ...     {
    ...         "command": ["./a_program"],
    ...         "output": ["fake_one"],
    ...         "returncode": 1
    ...     },
    ...     {
    ...         "command": ["./a_program"],
    ...         "output": ["fake_two"],
    ...         "returncode": 2
    ...     }
    ... ])

    >>> output = []
    >>> process.run(["./a_program"], output=output.append)
    1
    >>> output
    ['fake_one']

    >>> output = []
    >>> process.run(["./a_program"], output=output.append)
    2
    >>> output
    ['fake_two']
    """

    def __init__(self, subprocess):
        Observable.__init__(self)
        self.subprocess = subprocess

    def run(self, command, output=lambda x: None):
        self.notify("PROCESS", command)
        process = self.subprocess.Popen(
            command,
            stdout=self.subprocess.PIPE,
            stderr=self.subprocess.STDOUT,
            text=True
        )
        for line in process.stdout:
            output(line.rstrip("\r\n"))
        process.wait()
        return process.returncode

    @staticmethod
    def create():
        return Process(subprocess=subprocess)

    @staticmethod
    def create_null(responses=[]):
        class NullSubprocess:
            PIPE = None
            STDOUT = None
            def Popen(self, command, stdout, stderr, text):
                response = {"returncode": 0, "output": []}
                for i in range(len(responses)):
                    if responses[i]["command"] == command:
                        response = dict(response, **responses.pop(i))
                        break
                return NullProcess(
                    returncode=response["returncode"],
                    output=response["output"],
                )
        class NullProcess:
            def __init__(self, returncode, output):
                self.returncode = returncode
                self.stdout = output
            def wait(self):
                pass
        return Process(subprocess=NullSubprocess())

class Terminal(Observable):

    """
    I am an infrastructure wrapper for printing text to a terminal.

    I write text to stdout:

    >>> subprocess.run([
    ...     "python", "-c",
    ...     "from rlci.infrastructure import Terminal;"
    ...         "Terminal.create().print_line('hello')"
    ... ], stdout=subprocess.PIPE).stdout
    b'hello\\n'

    The null version of me doesn't write anything to stdout:

    >>> subprocess.run([
    ...     "python", "-c",
    ...     "from rlci.infrastructure import Terminal;"
    ...         "Terminal.create_null().print_line('hello')"
    ... ], stdout=subprocess.PIPE).stdout
    b''

    I log the lines that I print:

    >>> events = Events()
    >>> terminal = events.listen(Terminal.create_null())
    >>> terminal.print_line("hello")
    >>> events
    STDOUT => 'hello'
    """

    def __init__(self, stdout):
        Observable.__init__(self)
        self.stdout = stdout

    def print_line(self, text):
        self.notify("STDOUT", text)
        self.stdout.write(text)
        self.stdout.write("\n")
        self.stdout.flush()

    @staticmethod
    def create():
        return Terminal(stdout=sys.stdout)

    @staticmethod
    def create_null():
        class NullStream:
            def write(self, text):
                pass
            def flush(self):
                pass
        return Terminal(NullStream())

class Args:

    """
    I am an infrastructure wrapper for reading program arguments (via the sys
    module).

    I return the arguments passed to the program:

    >>> print(subprocess.run([
    ...     "python", "-c",
    ...     "from rlci.infrastructure import Args;"
    ...         "print(Args.create().get())",
    ...     "arg1", "arg2"
    ... ], stdout=subprocess.PIPE, text=True).stdout.strip())
    ['arg1', 'arg2']

    The null version of me does not read arguments passed to the program, but
    instead returns configured arguments:

    >>> print(subprocess.run([
    ...     "python", "-c",
    ...     "from rlci.infrastructure import Args;"
    ...         "print(Args.create_null(['configured']).get())",
    ...     "arg1", "arg2"
    ... ], stdout=subprocess.PIPE, text=True).stdout.strip())
    ['configured']
    """

    def __init__(self, sys):
        self.sys = sys

    def get(self):
        return self.sys.argv[1:]

    @staticmethod
    def create():
        return Args(sys=sys)

    @staticmethod
    def create_null(args):
        class NullSys:
            argv = [None]+args
        return Args(NullSys())

class SocketSerializer:

    def write_object(self, socket, obj):
        return socket.sendall(obj)

    def read_object(self, socket):
        return socket.recv(1024)

class UnixDomainSocketServer(Observable, SocketSerializer):

    """
    I am an infrastructure wrapper for a Unix domain socket server.

    An echo server can be created like this:

    >>> server_process = subprocess.Popen([
    ...     "python", "rlci-server-listen.py",
    ...     "/tmp/test-server.socket",
    ...     "python", "-c",
    ...     "from rlci.infrastructure import UnixDomainSocketServer;"
    ...     "handler = lambda x: x;"
    ...     "server = UnixDomainSocketServer.create();"
    ...     "server.register_handler(handler);"
    ...     "server.start();"
    ... ])
    >>> time.sleep(0.5)

    And queried with a client like this:

    >>> client = UnixDomainSocketClient.create()
    >>> client.send_request("/tmp/test-server.socket", b"test")
    b'test'

    The null version of me simulates a request coming in:

    >>> server = UnixDomainSocketServer.create_null(simulate_request=b"hello")
    >>> server.register_handler(print)
    >>> server.start()
    b'hello'

    I log responses:

    >>> events = Events()
    >>> server = events.listen(UnixDomainSocketServer.create_null(simulate_request=b"hello"))
    >>> server.register_handler(lambda x: x*2)
    >>> server.start()
    >>> events
    SERVER_RESPONSE => b'hellohello'
    """

    def __init__(self, os, socket):
        Observable.__init__(self)
        self.os = os
        self.socket = socket

    def register_handler(self, handler):
        self.handler = handler

    def start(self):
        s = self.socket.socket(fileno=0, family=self.socket.AF_UNIX)
        s.listen()
        connection, address = s.accept()
        request = self.read_object(connection)
        response = self.handler(request)
        self.notify("SERVER_RESPONSE", response)
        self.write_object(connection, response)

    @staticmethod
    def create():
        return UnixDomainSocketServer(os=os, socket=socket)

    @staticmethod
    def create_null(simulate_request):
        class NullOs:
            def remove(self, path):
                pass
        class NullSocketModule:
            AF_UNIX = object()
            def socket(self, family, fileno):
                return NullSocket()
        class NullSocket:
            def bind(self, address):
                pass
            def listen(self):
                pass
            def accept(self):
                return (NullConnection(), None)
        class NullConnection:
            def recv(self, bufsize):
                return simulate_request
            def sendall(self, bytes):
                pass
        return UnixDomainSocketServer(os=NullOs(), socket=NullSocketModule())

class UnixDomainSocketClient(Observable, SocketSerializer):

    """
    I am an infrastructure wrapper for a Unix domain socket client.

    Given a server:

    >>> server_process = subprocess.Popen([
    ...     "python", "rlci-server-listen.py",
    ...     "/tmp/test-server.socket",
    ...     "python", "-c",
    ...     "from rlci.infrastructure import UnixDomainSocketServer;"
    ...     "handler = lambda x: x;"
    ...     "server = UnixDomainSocketServer.create();"
    ...     "server.register_handler(handler);"
    ...     "server.start();"
    ... ])
    >>> time.sleep(0.5)

    I can query it like this:

    >>> client = UnixDomainSocketClient.create()
    >>> client.send_request("/tmp/test-server.socket", b"test")
    b'test'

    The null version does not connect to the real socket:

    >>> c = UnixDomainSocketClient.create_null()
    >>> _ = c.send_request("/tmp/some-path-that-does-not-exist.socket", b"data")

    The null version returns configured responses:

    >>> c = UnixDomainSocketClient.create_null(responses=[b'first', b'second'])
    >>> c.send_request("/tmp/some-path-that-does-not-exist.socket", b"data")
    b'first'
    >>> c.send_request("/tmp/some-path-that-does-not-exist.socket", b"data")
    b'second'

    I log requests:

    >>> events = Events()
    >>> c = events.listen(UnixDomainSocketClient.create_null())
    >>> _ = c.send_request("/tmp/path.socket", b"data")
    >>> events
    SERVER_REQUEST => ('/tmp/path.socket', b'data')
    """

    def __init__(self, socket):
        Observable.__init__(self)
        self.socket = socket

    def send_request(self, path, request):
        s = self.socket.socket(self.socket.AF_UNIX)
        s.connect(path)
        self.notify("SERVER_REQUEST", (path, request))
        self.write_object(s, request)
        return self.read_object(s)

    @staticmethod
    def create_null(responses=[]):
        class NullSocketModule:
            AF_UNIX = object()
            def socket(self, family):
                return NullSocket()
        class NullSocket:
            def connect(self, path):
                pass
            def sendall(self, data):
                pass
            def recv(self, bufsize):
                if responses:
                    if isinstance(responses[0], Exception):
                        raise responses.pop(0)
                    return responses.pop(0)
                else:
                    return b''
        return UnixDomainSocketClient(socket=NullSocketModule())

    @staticmethod
    def create():
        return UnixDomainSocketClient(socket=socket)
