import sys

from rlci.events import Observable, Events
from rlci.pipelines import Engine, Runtime
from rlci.infrastructure import Args, Terminal

class RLCIApp:

    """
    I am a tool to facilitate CI/CD.

    I can trigger a predefined pipeline:

    >>> RLCIApp.run_in_test_mode(args=["trigger"]).filter("STDOUT")
    STDOUT => 'Triggered RLCIPipeline'

    In the above test test, we just want to assert that a pipeline was
    triggered. We don't care about the details of how it was run. (For
    that, see Engine.) How can we "externally" observe that a pipeline
    was run? We choose to only look at what was printed to stdout. In
    the future this might change. We might replace the stdout print
    with a write to a database instead.

    I fail when given other args:

    >>> RLCIApp.run_in_test_mode(args=[])
    STDOUT => 'Usage: python3 rlci.py trigger'
    EXIT => 1

    The real app can be instantiated:

    >>> isinstance(RLCIApp.create(), RLCIApp)
    True
    """

    def __init__(self, terminal, args, runtime):
        self.terminal = terminal
        self.args = args
        self.runtime = runtime

    def run(self):
        if self.args.get() == ["trigger"]:
            Engine(
                runtime=self.runtime,
                terminal=self.terminal
            ).trigger()
        else:
            self.terminal.print_line("Usage: python3 rlci.py trigger")
            sys.exit(1)

    @staticmethod
    def create():
        return RLCIApp(
            terminal=Terminal.create(),
            args=Args.create(),
            runtime=Runtime()
        )

    @staticmethod
    def run_in_test_mode(args=[]):
        events = Events()
        try:
            RLCIApp(
                terminal=events.listen(Terminal.create_null()),
                args=Args.create_null(args),
                runtime=events.listen(Runtime.create_null())
            ).run()
        except SystemExit as e:
            events.append(("EXIT", e.code))
        return events
