import subprocess
import sys

from rlci.events import Observable, Events
from rlci.pipelines import Engine, Runtime

class RLCIApp:

    """
    I am a tool to facilitate CI/CD.

    I can trigger a predefined pipeline:

    >>> RLCIApp.run_in_test_mode(args=["trigger"])
    TRIGGER => 'RLCIPipeline'

    I fail when given other args:

    >>> RLCIApp.run_in_test_mode(args=[])
    STDOUT => 'Usage: python3 rlci.py trigger'
    EXIT => 1
    """

    def __init__(self, terminal=None, args=None, pipeline_engine=None):
        self.terminal = Terminal() if terminal is None else terminal
        self.args = Args() if args is None else args
        self.pipeline_engine = Engine() if pipeline_engine is None else pipeline_engine

    def run(self):
        if self.args.get() == ["trigger"]:
            self.pipeline_engine.trigger("RLCIPipeline")
        else:
            self.terminal.print_line("Usage: python3 rlci.py trigger")
            sys.exit(1)

    @staticmethod
    def run_in_test_mode(args=[]):
        events = Events()
        terminal = Terminal.create_null()
        terminal.register_event_listener(events)
        pipeline_engine = Engine(runtime=Runtime.create_null())
        pipeline_engine.register_event_listener(events)
        app = RLCIApp(
            terminal=terminal,
            args=Args.create_null(args),
            pipeline_engine=pipeline_engine
        )
        try:
            app.run()
        except SystemExit as e:
            events.append(("EXIT", e.code))
        return events

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
