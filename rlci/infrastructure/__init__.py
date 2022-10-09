import os
import socket
import subprocess
import sys
import tempfile
import time

from rlci.events import Observable, Events
from rlci.infrastructure.filesystem import Filesystem

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

    >>> process = Process.create_null()
    >>> events = Events.capture_from(process)
    >>> _ = process.run(["echo", "hello"])
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

    >>> terminal = Terminal.create_null()
    >>> events = Events.capture_from(terminal)
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

    >>> tmp_dir = tempfile.TemporaryDirectory()
    >>> tmp_socket = os.path.join(tmp_dir.name, "tmp.socket")
    >>> server_process = subprocess.Popen([
    ...     "python", "rlci-server-listen.py",
    ...     tmp_socket,
    ...     "python", "-c",
    ...     "from rlci.infrastructure import UnixDomainSocketServer;"
    ...     "handler = lambda x: x;"
    ...     "server = UnixDomainSocketServer.create();"
    ...     "server.register_handler(handler);"
    ...     "server.start();"
    ... ])

    And queried with a client like this:

    >>> try:
    ...     client = UnixDomainSocketClient.create()
    ...     client.send_request(tmp_socket, b"test")
    ... finally:
    ...     server_process.kill()
    b'test'

    The null version of me simulates a request coming in:

    >>> server = UnixDomainSocketServer.create_null(simulate_request=b"hello")
    >>> server.register_handler(print)
    >>> server.start()
    b'hello'

    I log responses:

    >>> server = UnixDomainSocketServer.create_null(simulate_request=b"hello")
    >>> events = Events.capture_from(server)
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
        s = self.socket.socket(fileno=0)
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
            def socket(self, fileno):
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

    >>> tmp_dir = tempfile.TemporaryDirectory()
    >>> tmp_socket = os.path.join(tmp_dir.name, "tmp.socket")
    >>> server_process = subprocess.Popen([
    ...     "python", "rlci-server-listen.py",
    ...     tmp_socket,
    ...     "python", "-c",
    ...     "from rlci.infrastructure import UnixDomainSocketServer;"
    ...     "handler = lambda x: x;"
    ...     "server = UnixDomainSocketServer.create();"
    ...     "server.register_handler(handler);"
    ...     "server.start();"
    ... ])

    I can query it like this:

    >>> try:
    ...     client = UnixDomainSocketClient.create()
    ...     client.send_request(tmp_socket, b"test")
    ... finally:
    ...     server_process.kill()
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

    >>> c = UnixDomainSocketClient.create_null()
    >>> events = Events.capture_from(c)
    >>> _ = c.send_request("/tmp/path.socket", b"data")
    >>> events
    SERVER_REQUEST => ('/tmp/path.socket', b'data')
    """

    def __init__(self, socket):
        Observable.__init__(self)
        self.socket = socket

    def send_request(self, path, request):
        s = self.socket.socket(self.socket.AF_UNIX)
        retry_delays = [0.01, 0.05, 0.10, 0.20, 0.50, 1.00, 2.00]
        while True:
            try:
                s.connect(path)
                break
            except (ConnectionRefusedError, FileNotFoundError):
                if retry_delays:
                    time.sleep(retry_delays.pop(0))
                else:
                    raise
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
