import subprocess
import sys

from rlci.events import Observable, Events

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
