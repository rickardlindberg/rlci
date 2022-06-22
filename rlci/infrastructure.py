import queue
import subprocess
import sys
import threading

from rlci.events import Observable, Events

class Process(Observable):

    """
    I am an infrastructure wrapper for running processes.

    I run a process and return its exit code:

    >>> Process.create().run(["bash", "-c", "exit 99"])
    99

    I stream stdout/stderr:

    >>> stdout = []
    >>> stderr = []
    >>> _ = Process.create().run(
    ...     ["bash", "-c", "echo one; echo two 1>&2"],
    ...     stdout=stdout.append, stderr=stderr.append
    ... )
    >>> stdout
    ['one']
    >>> stderr
    ['two']

    I log the process I run:

    >>> events = Events()
    >>> _ = events.listen(Process.create_null()).run(["echo", "hello"])
    >>> events
    PROCESS => ['echo', 'hello']

    The null version of me does not run any process:

    >>> Process.create_null().run(["bash", "-c", "exit 99"])
    0
    """

    def __init__(self, subprocess, threading):
        Observable.__init__(self)
        self.subprocess = subprocess
        self.threading = threading

    def run(self, command, stdout=lambda x: None, stderr=lambda x: None):
        def stream_reader_thread(stream, listener):
            try:
                for line in stream:
                    command_queue.put((listener, line.rstrip("\r\n")))
            finally:
                command_queue.put((ends.remove, listener))
        self.notify("PROCESS", command)
        process = self.subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        command_queue = queue.Queue()
        ends = [stdout, stderr]
        self._start_thread(stream_reader_thread, (process.stdout, stdout))
        self._start_thread(stream_reader_thread, (process.stderr, stderr))
        while ends:
            fn, arg = command_queue.get()
            fn(arg)
        process.wait()
        return process.returncode

    def _start_thread(self, target, args):
        self.threading.Thread(target=target, args=args).start()

    @staticmethod
    def create_null():
        PIPE = None
        class NullSubprocess:
            def Popen(self, command, stdout, stderr, text):
                return NullProcess()
        class NullProcess:
            returncode = 0
            stdout = []
            stderr = []
            def wait(self):
                pass
        class NullThreading:
            def Thread(self, target, args):
                return NullThread(target, args)
        class NullThread:
            def __init__(self, target, args):
                self.target = target
                self.args = args
            def start(self):
                self.target(*self.args)
        return Process(subprocess=NullSubprocess(), threading=NullThreading())

    @staticmethod
    def create():
        return Process(subprocess=subprocess, threading=threading)

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
