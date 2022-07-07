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
    ...    ],
    ...    ('python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', 'git', 'rev-parse'): [
    ...        {"output": ["<git-commit>"]}
    ...    ],
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
    STDOUT => "['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', 'git', 'rev-parse']"
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', 'git', 'rev-parse']
    STDOUT => '<git-commit>'
    STDOUT => "['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', './zero.py', 'deploy', '<git-commit>']"
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/workspace', './zero.py', 'deploy', '<git-commit>']
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
        self.process = ProcessWithLogging(terminal, process)

    def trigger(self):
        try:
            self.terminal.print_line("Triggered RLCIPipeline")
            with Workspace(self.process) as workspace:
                workspace.run(["git", "clone", "git@github.com:rickardlindberg/rlci.git", "."])
                workspace.run(["git", "merge", "--no-ff", "-m", "Integrate.", "origin/BRANCH"])
                workspace.run(["./zero.py", "build"])
                workspace.run(["git", "push"])
                version = workspace.slurp(["git", "rev-parse"])
                workspace.run(["./zero.py", "deploy", version])
                return True
        except CommandFailure:
            self.terminal.print_line(f"FAIL")
            return False

class Workspace:

    def __init__(self, process):
        self.process = process

    def __enter__(self):
        self.workspace = self.process.slurp(["mktemp", "-d"])
        return ProcessInDirectory(self.process, self.workspace)

    def __exit__(self, type, value, traceback):
        self.process.run(["rm", "-rf", self.workspace])

class ProcessInDirectory:

    def __init__(self, process, directory):
        self.process = process
        self.directory = directory

    def slurp(self, command):
        return self.process.slurp(self.create_command(command))

    def run(self, command):
        self.process.run(self.create_command(command))

    def create_command(self, command):
        return [
            "python3",
            "-c",
            "; ".join([
                "import sys",
                "import os",
                "os.chdir(sys.argv[1])",
                "os.execvp(sys.argv[2], sys.argv[2:])",
            ]),
            self.directory
        ] + command

class ProcessWithLogging:

    def __init__(self, terminal, process):
        self.terminal = terminal
        self.process = process

    def slurp(self, command):
        output = []
        self.run(command, output=output.append)
        return " ".join(output)

    def run(self, command, output=lambda x: None):
        def log(line):
            self.terminal.print_line(line)
            output(line)
        self.terminal.print_line(repr(command))
        if self.process.run(command, output=log) != 0:
            raise CommandFailure()

class CommandFailure(Exception):
    pass
