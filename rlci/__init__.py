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

    DESIGN NOTE: In the above test test, we just want to assert that the
    predefined pipeline was triggered. We don't care about the details of how
    it was run. How can we "externally" observe that it was run?  We choose to
    only look at what was printed to stdout. In the future this might change.
    We might replace the print to stdout with a write to a database for
    example.

    I exit with 0 if the pipeline ran successfully:

    >>> RLCIApp.run_in_test_mode(args=["trigger"]).filter("EXIT")
    EXIT => 0

    I exit with 1 if the pipeline failed:

    >>> RLCIApp.run_in_test_mode(args=["trigger"], process_responses={
    ...    ('mktemp', '-d'): [{'returncode': 1}],
    ... }).filter("EXIT")
    EXIT => 1

    DESIGN NOTE: In the above test we need to configure a pipeline to fail. At
    the moment, this requires information about commands run by the pipeline.
    Can we move that detail out of this test?

    ## Other

    I fail when given unknown arguments:

    >>> RLCIApp.run_in_test_mode(args=[])
    STDOUT => 'Usage: python3 rlci.py trigger'
    EXIT => 1

    ## Internal health checks

    The real app can be created:

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
