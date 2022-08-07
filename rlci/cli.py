import sys

from rlci.events import Observable, Events
from rlci.engine import Engine, DB, Workspace, ProcessInDirectory
from rlci.infrastructure import Args, Terminal, Process, Filesystem

class CLI:

    """
    I am a command line interface to RLCI.

    Pipeline triggering
    ===================

    I can trigger different pipelines:

    >>> CLI.run_in_test_mode(
    ...     args=["trigger", "rlci"]
    ... ).has("STDOUT", "Triggered RLCIPipeline")
    True

    >>> CLI.run_in_test_mode(
    ...     args=["trigger", "test-pipeline"]
    ... ).has("STDOUT", "Triggered TEST-PIPELINE")
    True

    DESIGN NOTE: In the above test tests, we just want to assert that the
    pipelines were triggered. We don't care about the details of how they were
    run. How can we "externally" observe that they were run? We choose to only
    look at what was printed to stdout. In the future this might change. We
    might replace the print to stdout with a write to a database for example.

    I exit with 0 when a triggered pipeline succeeds:

    >>> CLI.run_in_test_mode(args=["trigger", "rlci"]).filter("EXIT")
    EXIT => 0

    I exit with 1 when a triggered pipeline fails:

    >>> CLI.run_in_test_mode(
    ...     args=["trigger", "rlci"],
    ...     simulate_pipeline_failure=True
    ... ).filter("EXIT")
    EXIT => 1

    I exit with usage when no pipeline is given:

    >>> CLI.run_in_test_mode(args=["trigger"])
    STDOUT => 'Usage: python3 rlci-cli.py trigger <pipeline>'
    EXIT => 1

    Other
    =====

    I fail when given unknown arguments:

    >>> CLI.run_in_test_mode(args=[])
    STDOUT => 'Usage: python3 rlci-cli.py trigger'
    EXIT => 1

    Internal health checks
    ======================

    The real app can be created:

    >>> isinstance(CLI.create(), CLI)
    True
    """

    def __init__(self, terminal, args, process, db, filesystem):
        self.terminal = terminal
        self.args = args
        self.process = process
        self.db = db
        self.filesystem = filesystem

    def run(self):
        if self.args.get() == ["trigger"]:
            self.terminal.print_line("Usage: python3 rlci-cli.py trigger <pipeline>")
            sys.exit(1)
        elif self.args.get()[:1] == ["trigger"]:
            self.trigger(self.args.get()[1])
        else:
            self.terminal.print_line("Usage: python3 rlci-cli.py trigger")
            sys.exit(1)

    def trigger(self, name):
        successful = Engine(
            terminal=self.terminal,
            process=self.process,
            db=self.db,
            filesystem=self.filesystem
        ).trigger(name)
        sys.exit(0 if successful else 1)

    @staticmethod
    def create():
        return CLI(
            terminal=Terminal.create(),
            args=Args.create(),
            process=Process.create(),
            db=DB.create(),
            filesystem=Filesystem.create()
        )

    @staticmethod
    def run_in_test_mode(args=[], simulate_pipeline_failure=False):
        events = Events()
        process_responses = []
        if simulate_pipeline_failure:
            process_responses.append({
                "command": Workspace.create_create_command(),
                "returncode": 99,
            })
        try:
            CLI(
                terminal=events.listen(Terminal.create_null()),
                args=Args.create_null(args),
                process=events.listen(Process.create_null(responses=process_responses)),
                db=DB.create_in_memory(),
                filesystem=Filesystem.create_in_memory()
            ).run()
        except SystemExit as e:
            events.append(("EXIT", e.code))
        return events
