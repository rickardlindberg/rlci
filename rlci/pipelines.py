from rlci.events import Events
from rlci.infrastructure import Terminal, Process

class Engine:

    """
    I am the engine that runs pipelines.

    I can trigger a pre-defined pipeline:

    >>> events = Events()
    >>> terminal = events.listen(Terminal.create_null())
    >>> process = events.listen(Process.create_null(responses={
    ...    ('mktemp', '-d'): [
    ...        {"output": ["/tmp/workspace"]}
    ...    ]
    ... }))
    >>> Engine(terminal=terminal, process=process).trigger()
    True
    >>> events
    STDOUT => 'Triggered RLCIPipeline'
    STDOUT => "['mktemp', '-d']"
    PROCESS => ['mktemp', '-d']
    STDOUT => '/tmp/workspace'
    STDOUT => "['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', 'git', 'clone', 'git@github.com:rickardlindberg/rlci.git', '.']"
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', 'git', 'clone', 'git@github.com:rickardlindberg/rlci.git', '.']
    STDOUT => "['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', 'git', 'merge', '--no-ff', '-m', 'Integrate.', 'origin/BRANCH']"
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', 'git', 'merge', '--no-ff', '-m', 'Integrate.', 'origin/BRANCH']
    STDOUT => "['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', './zero.py', 'build']"
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', './zero.py', 'build']
    STDOUT => "['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', 'git', 'push']"
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', 'git', 'push']
    STDOUT => "['rm', '-rf', '/tmp/workspace']"
    PROCESS => ['rm', '-rf', '/tmp/workspace']

    Pipeline is aborted if process fails:

    >>> events = Events()
    >>> terminal = events.listen(Terminal.create_null())
    >>> process = events.listen(Process.create_null(responses={
    ...    ('mktemp', '-d'): [
    ...        {"returncode": 1}
    ...    ],
    ... }))
    >>> Engine(terminal=terminal, process=process).trigger()
    False
    >>> events
    STDOUT => 'Triggered RLCIPipeline'
    STDOUT => "['mktemp', '-d']"
    PROCESS => ['mktemp', '-d']
    STDOUT => 'FAIL'
    """

    def __init__(self, terminal, process):
        self.terminal = terminal
        self.process = process

    def trigger(self):
        self.terminal.print_line(f"Triggered RLCIPipeline")
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
            return True
        except StepFailure:
            self.terminal.print_line(f"FAIL")
            return False

    def _slurp(self, command):
        output = []
        self._run(command, output=output.append)
        return " ".join(output)

    def _run(self, command, output=lambda x: None):
        def log(line):
            self.terminal.print_line(line)
            output(line)
        self.terminal.print_line(repr(command))
        if self.process.run(command, output=log) != 0:
            raise StepFailure()

class StepFailure(Exception):
    pass
