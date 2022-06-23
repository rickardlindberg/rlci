import contextlib
import os
import subprocess
import tempfile

from rlci.events import Observable, Events
from rlci.infrastructure import Terminal, Process

class Runtime(Observable):

    """
    ## Workspace commands

    I can create empty workspaces:

    >>> events = Events()
    >>> runtime = events.listen(Runtime())
    >>> outside_before = os.listdir()
    >>> with runtime.workspace():
    ...     inside = os.listdir()
    >>> outside_after = os.listdir()
    >>> outside_before == outside_after
    True
    >>> inside
    []
    >>> events
    EMPTY_WORKSPACE => 'create'
    EMPTY_WORKSPACE => 'delete'
    """

    def __init__(self, subprocess=subprocess):
        Observable.__init__(self)
        self.subprocess = subprocess

    @contextlib.contextmanager
    def workspace(self):
        self.notify("EMPTY_WORKSPACE", "create")
        try:
            with tempfile.TemporaryDirectory() as d:
                current_dir = os.getcwd()
                try:
                    os.chdir(d)
                    yield
                finally:
                    os.chdir(current_dir)
        finally:
            self.notify("EMPTY_WORKSPACE", "delete")

    @staticmethod
    def create_null():
        class NullSubprocess:
            PIPE = None
            def run(self, *args, **kwargs):
                return NullResponse()
        class NullResponse:
            stdout = b''
        return Runtime(NullSubprocess())

class Engine:

    """
    I am the engine that runs pipelines.

    I can trigger a pre-defined pipeline:

    >>> events = Events()
    >>> runtime = events.listen(Runtime.create_null())
    >>> terminal = events.listen(Terminal.create_null())
    >>> process = events.listen(Process.create_null())
    >>> Engine(runtime=runtime, terminal=terminal, process=process).trigger()
    >>> events
    EMPTY_WORKSPACE => 'create'
    PROCESS => ['git', 'clone', 'git@github.com:rickardlindberg/rlci.git', '.']
    PROCESS => ['git', 'merge', '--no-ff', '-m', 'Integrate.', 'origin/BRANCH']
    PROCESS => ['./zero.py', 'build']
    PROCESS => ['git', 'push']
    EMPTY_WORKSPACE => 'delete'
    STDOUT => 'Triggered RLCIPipeline'

    Pipeline is aborted if process fails:

    >>> events = Events()
    >>> runtime = events.listen(Runtime.create_null())
    >>> terminal = events.listen(Terminal.create_null())
    >>> process = events.listen(Process.create_null({
    ...    ('git', 'clone', 'git@github.com:rickardlindberg/rlci.git', '.'): [
    ...        {"returncode": 1}
    ...    ]
    ... }))
    >>> Engine(runtime=runtime, terminal=terminal, process=process).trigger()
    >>> events
    EMPTY_WORKSPACE => 'create'
    PROCESS => ['git', 'clone', 'git@github.com:rickardlindberg/rlci.git', '.']
    EMPTY_WORKSPACE => 'delete'
    STDOUT => 'FAIL'
    """

    def __init__(self, runtime, terminal, process):
        self.runtime = runtime
        self.terminal = terminal
        self.process = process

    def trigger(self):
        try:
            with self.runtime.workspace():
                self._run(["git", "clone", "git@github.com:rickardlindberg/rlci.git", "."])
                self._run(["git", "merge", "--no-ff", "-m", "Integrate.", "origin/BRANCH"])
                self._run(["./zero.py", "build"])
                self._run(["git", "push"])
            self.terminal.print_line(f"Triggered RLCIPipeline")
        except StepFailure:
            self.terminal.print_line(f"FAIL")

    def _run(self, command):
        if self.process.run(command) != 0:
            raise StepFailure()

class StepFailure(Exception):
    pass
