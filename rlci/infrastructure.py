import subprocess
import sys

from rlci.events import Observable, Events

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
