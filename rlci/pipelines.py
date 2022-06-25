import contextlib
import os
import subprocess
import tempfile

from rlci.events import Observable, Events
from rlci.infrastructure import Terminal, Process

class Engine:

    """
    I am the engine that runs pipelines.

    I can trigger a pre-defined pipeline:

    >>> events = Events()
    >>> terminal = events.listen(Terminal.create_null())
    >>> process = events.listen(Process.create_null({
    ...    ('mktemp', '-d'): [
    ...        {"stdout": ["/tmp/workspace"]}
    ...    ]
    ... }))
    >>> Engine(terminal=terminal, process=process).trigger()
    >>> events
    PROCESS => ['mktemp', '-d']
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', 'git', 'clone', 'git@github.com:rickardlindberg/rlci.git', '.']
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', 'git', 'merge', '--no-ff', '-m', 'Integrate.', 'origin/BRANCH']
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', './zero.py', 'build']
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', 'git', 'push']
    PROCESS => ['rm', '-rf', '/tmp/workspace']
    STDOUT => 'Triggered RLCIPipeline'

    Pipeline is aborted if process fails:

    >>> events = Events()
    >>> terminal = events.listen(Terminal.create_null())
    >>> process = events.listen(Process.create_null({
    ...    ('python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', 'git', 'clone', 'git@github.com:rickardlindberg/rlci.git', '.'): [
    ...        {"returncode": 1}
    ...    ],
    ...    ('mktemp', '-d'): [
    ...        {"stdout": ["/tmp/workspace"]}
    ...    ],
    ... }))
    >>> Engine(terminal=terminal, process=process).trigger()
    >>> events
    PROCESS => ['mktemp', '-d']
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', 'git', 'clone', 'git@github.com:rickardlindberg/rlci.git', '.']
    PROCESS => ['rm', '-rf', '/tmp/workspace']
    STDOUT => 'FAIL'
    """

    def __init__(self, terminal, process):
        self.terminal = terminal
        self.process = process

    def trigger(self):
        try:
            workspace = self._slurp(["mktemp", "-d"])
            try:
                prefix = ["python3", "-c", "import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])", workspace]
                self._run(prefix+["git", "clone", "git@github.com:rickardlindberg/rlci.git", "."])
                self._run(prefix+["git", "merge", "--no-ff", "-m", "Integrate.", "origin/BRANCH"])
                self._run(prefix+["./zero.py", "build"])
                self._run(prefix+["git", "push"])
            finally:
                self._run(["rm", "-rf", workspace])
            self.terminal.print_line(f"Triggered RLCIPipeline")
        except StepFailure:
            self.terminal.print_line(f"FAIL")

    def _slurp(self, command):
        stdout = []
        self._run(command, stdout=stdout.append)
        return " ".join(stdout)

    def _run(self, command, **kwargs):
        if self.process.run(command, **kwargs) != 0:
            raise StepFailure()

class StepFailure(Exception):
    pass
