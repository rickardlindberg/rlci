import sys

from rlci.events import Observable, Events
from rlci.pipelines import Engine
from rlci.infrastructure import Args, Terminal, Process

class RLCIApp:

    """
    I am a tool to facilitate CI/CD.

    ## Pipeline triggering

    I can trigger a predefined pipeline:

    >>> RLCIApp.run_in_test_mode(args=["trigger"]).filter("STDOUT")[0][1]
    'Triggered RLCIPipeline'

    In the above test test, we just want to assert that a pipeline was
    triggered. We don't care about the details of how it was run. (For
    that, see Engine.) How can we "externally" observe that a pipeline
    was run? We choose to only look at what was printed to stdout. In
    the future this might change. We might replace the stdout print
    with a write to a database instead.

    I exit with status code from pipeline run:

    >>> RLCIApp.run_in_test_mode(args=["trigger"]).filter("EXIT")
    EXIT => 0

    >>> RLCIApp.run_in_test_mode(args=["trigger"], process_responses={
    ...    ('mktemp', '-d'): [{'returncode': 1}],
    ... }).filter("EXIT")
    EXIT => 1

    ## Other

    I fail when given other args:

    >>> RLCIApp.run_in_test_mode(args=[])
    STDOUT => 'Usage: python3 rlci.py trigger'
    EXIT => 1

    ## Internal health checks

    The real app can be instantiated:

    >>> isinstance(RLCIApp.create(), RLCIApp)
    True
    """

    def __init__(self, terminal, args, process):
        self.terminal = terminal
        self.args = args
        self.process = process

    def run(self):
        if self.args.get() == ["trigger"]:
            successful = Engine(
                terminal=self.terminal,
                process=self.process
            ).trigger()
            sys.exit(0 if successful else 1)
        else:
            self.terminal.print_line("Usage: python3 rlci.py trigger")
            sys.exit(1)

    @staticmethod
    def create():
        return RLCIApp(
            terminal=Terminal.create(),
            args=Args.create(),
            process=Process.create()
        )

    @staticmethod
    def run_in_test_mode(args=[], process_responses={}):
        events = Events()
        try:
            RLCIApp(
                terminal=events.listen(Terminal.create_null()),
                args=Args.create_null(args),
                process=events.listen(Process.create_null(responses=process_responses))
            ).run()
        except SystemExit as e:
            events.append(("EXIT", e.code))
        return events
