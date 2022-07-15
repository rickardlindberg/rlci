import sys

from rlci.events import Observable, Events
from rlci.pipelines import Engine, DB, Workspace, ProcessInDirectory
from rlci.infrastructure import Args, Terminal, Process

class RLCIApp:

    """
    I am a tool to facilitate CI/CD.

    ## Pipeline triggering

    I can trigger different pipelines:

    >>> RLCIApp.run_in_test_mode(
    ...     args=["trigger", "rlci"]
    ... ).has("STDOUT", "Triggered RLCIPipeline")
    True

    >>> RLCIApp.run_in_test_mode(
    ...     args=["trigger", "test-pipeline"]
    ... ).has("STDOUT", "Triggered TEST-PIPELINE")
    True

    DESIGN NOTE: In the above test tests, we just want to assert that the
    predefined pipeline was triggered. We don't care about the details of how
    it was run. How can we "externally" observe that it was run? We choose to
    only look at what was printed to stdout. In the future this might change.
    We might replace the print to stdout with a write to a database for
    example.

    I exit with 0 if a triggered pipeline succeeds:

    >>> RLCIApp.run_in_test_mode(args=["trigger", "rlci"]).filter("EXIT")
    EXIT => 0

    I exit with 1 if a triggered pipeline fails:

    >>> RLCIApp.run_in_test_mode(
    ...     args=["trigger", "rlci"],
    ...     simulate_pipeline_failure=True
    ... ).filter("EXIT")
    EXIT => 1

    I exit with usage when given no pipeline:

    >>> RLCIApp.run_in_test_mode(args=["trigger"])
    STDOUT => 'Usage: python3 rlci.py trigger <pipeline>'
    EXIT => 1

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

    def __init__(self, terminal, args, process, db):
        self.terminal = terminal
        self.args = args
        self.process = process
        self.db = db
        self.db.save_pipeline("rlci", rlci_pipeline())
        self.db.save_pipeline("test-pipeline", {"name": "TEST-PIPELINE", "steps": []})

    def run(self):
        if self.args.get() == ["trigger"]:
            self.terminal.print_line("Usage: python3 rlci.py trigger <pipeline>")
            sys.exit(1)
        elif self.args.get()[:1] == ["trigger"]:
            self.trigger(self.args.get()[1])
        else:
            self.terminal.print_line("Usage: python3 rlci.py trigger")
            sys.exit(1)

    def trigger(self, name):
        successful = Engine(
            terminal=self.terminal,
            process=self.process,
            db=self.db
        ).trigger(name)
        sys.exit(0 if successful else 1)

    @staticmethod
    def create():
        return RLCIApp(
            terminal=Terminal.create(),
            args=Args.create(),
            process=Process.create(),
            db=DB.create()
        )

    @staticmethod
    def run_in_test_mode(args=[], process_responses={}, simulate_pipeline_failure=False):
        events = Events()
        if simulate_pipeline_failure:
            process_responses = {
               tuple(Workspace.create_create_command()): [{'returncode': 1}],
            }
        else:
            process_responses = {}
        try:
            RLCIApp(
                terminal=events.listen(Terminal.create_null()),
                args=Args.create_null(args),
                process=events.listen(Process.create_null(responses=process_responses)),
                db=DB.create_in_memory()
            ).run()
        except SystemExit as e:
            events.append(("EXIT", e.code))
        return events

def rlci_pipeline():
    """
    >>> Engine.trigger_in_test_mode(
    ...     rlci_pipeline(),
    ...     responses={
    ...         tuple(Workspace.create_create_command()): [
    ...             {"output": ["/tmp/workspace"]}
    ...         ],
    ...         tuple(ProcessInDirectory.create_command(['git', 'rev-parse', 'HEAD'], '/tmp/workspace')): [
    ...             {"output": ["<git-commit>"]}
    ...         ],
    ...     }
    ... )["events"].filter("PROCESS") # doctest: +ELLIPSIS
    PROCESS => ['mktemp', '-d']
    PROCESS => [..., 'git', 'clone', 'git@github.com:rickardlindberg/rlci.git', '.']
    PROCESS => [..., 'git', 'merge', '--no-ff', '-m', 'Integrate.', 'origin/BRANCH']
    PROCESS => [..., './zero.py', 'build']
    PROCESS => [..., 'git', 'push']
    PROCESS => [..., 'git', 'rev-parse', 'HEAD']
    PROCESS => [..., './zero.py', 'deploy', '<git-commit>']
    PROCESS => ['rm', '-rf', '/tmp/workspace']
    """
    return {
        "name": "RLCIPipeline",
        "steps": [
            {"command": ["git", "clone", "git@github.com:rickardlindberg/rlci.git", "."]},
            {"command": ["git", "merge", "--no-ff", "-m", "Integrate.", "origin/BRANCH"]},
            {"command": ["./zero.py", "build"]},
            {"command": ["git", "push"]},
            {"command": ["git", "rev-parse", "HEAD"], "variable": "version"},
            {"command": ["./zero.py", "deploy", {"variable": "version"}]},
        ],
    }
