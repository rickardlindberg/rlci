import subprocess
import sys

from rlci.events import Observable

class RLCIApp:

    """
    I am a tool to facilitate CI/CD.

    I can trigger a predefined pipeline:

    >>> RLCIApp.run_in_test_mode(args=["trigger"])
    SH => 'git clone git@github.com:rickardlindberg/rlci.git .'
    SH => 'git merge --no-ff -m "Integrate." origin/BRANCH'
    SH => './zero.py build'
    SH => 'git push'

    I fail when given other args:

    >>> RLCIApp.run_in_test_mode(args=[])
    STDOUT => 'Usage: python3 rlci.py trigger'
    EXIT => 1
    """

    def __init__(self, terminal=None, args=None, pipeline=None):
        self.terminal = Terminal() if terminal is None else terminal
        self.args = Args() if args is None else args
        self.pipeline = Pipeline() if pipeline is None else pipeline

    def run(self):
        if self.args.get() == ["trigger"]:
            self.pipeline.sh("git clone git@github.com:rickardlindberg/rlci.git .")
            self.pipeline.sh("git merge --no-ff -m \"Integrate.\" origin/BRANCH")
            self.pipeline.sh("./zero.py build")
            self.pipeline.sh("git push")
        else:
            self.terminal.print_line("Usage: python3 rlci.py trigger")
            sys.exit(1)

    @staticmethod
    def run_in_test_mode(args=[]):
        events = Events()
        terminal = Terminal.create_null()
        terminal.register_event_listener(events)
        pipeline = Pipeline.create_null()
        pipeline.register_event_listener(events)
        app = RLCIApp(
            terminal=terminal,
            args=Args.create_null(args),
            pipeline=pipeline
        )
        try:
            app.run()
        except SystemExit as e:
            events.append(("EXIT", e.code))
        return events

class Pipeline(Observable):

    """
    I can run shell commands:

    >>> Pipeline().sh('echo hello')
    b'hello\\n'

    I fail if command fails:

    >>> Pipeline().sh('exit 1')
    Traceback (most recent call last):
        ...
    subprocess.CalledProcessError: Command 'exit 1' returned non-zero exit status 1.

    The null version of me, runs no shell commands:

    >>> Pipeline.create_null().sh('echo hello')
    b''

    I log commands:

    >>> events = Events()
    >>> pipeline = Pipeline.create_null()
    >>> pipeline.register_event_listener(events)
    >>> _ = pipeline.sh("echo hello")
    >>> events
    SH => 'echo hello'
    """

    def __init__(self, subprocess=subprocess):
        Observable.__init__(self)
        self.subprocess = subprocess

    def sh(self, command):
        self.notify("SH", command)
        return self.subprocess.run(command, shell=True,
        stdout=self.subprocess.PIPE, check=True).stdout

    @staticmethod
    def create_null():
        class NullSubprocess:
            PIPE = None
            def run(self, *args, **kwargs):
                return NullResponse()
        class NullResponse:
            stdout = b''
        return Pipeline(NullSubprocess())

class Events(list):

    def notify(self, event, data):
        self.append((event, data))

    def filter(self, event):
        return Events(x for x in self if x[0] == event)

    def __repr__(self):
        return "\n".join(f"{event} => {repr(data)}" for event, data in self)

class Terminal(Observable):

    """
    I represent a terminal emulator to which text can be printed.

    I write text to stdout:

    >>> subprocess.run([
    ...     "python", "-c",
    ...     "import rlci; rlci.Terminal().print_line('hello')"
    ... ], stdout=subprocess.PIPE, check=True).stdout
    b'hello\\n'

    The null version of me doesn't write anything to stdout:

    >>> subprocess.run([
    ...     "python", "-c",
    ...     "import rlci; rlci.Terminal.create_null().print_line('hello')"
    ... ], stdout=subprocess.PIPE, check=True).stdout
    b''

    I log the lines that I print:

    >>> events = Events()
    >>> terminal = Terminal.create_null()
    >>> terminal.register_event_listener(events)
    >>> terminal.print_line("hello")
    >>> events
    STDOUT => 'hello'
    """

    def __init__(self, stdout=sys.stdout):
        Observable.__init__(self)
        self.stdout = stdout

    def print_line(self, text):
        self.notify("STDOUT", text)
        self.stdout.write(text)
        self.stdout.write("\n")
        self.stdout.flush()

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

    >>> subprocess.run([
    ...     "python", "-c",
    ...     "import rlci; print(rlci.Args().get())",
    ...     "arg1", "arg2"
    ... ], stdout=subprocess.PIPE, check=True).stdout
    b"['arg1', 'arg2']\\n"

    The null version of me does not read arguments passed to the program, but
    instead return configured arguments:

    >>> subprocess.run([
    ...     "python", "-c",
    ...     "import rlci; print(rlci.Args.create_null(['configured1']).get())",
    ...     "arg1", "arg2"
    ... ], stdout=subprocess.PIPE, check=True).stdout
    b"['configured1']\\n"
    """

    def __init__(self, sys=sys):
        self.sys = sys

    def get(self):
        return self.sys.argv[1:]

    @staticmethod
    def create_null(args):
        class NullSys:
            argv = [None]+args
        return Args(NullSys())

if __name__ == "__main__":
    RLCIApp().run()
