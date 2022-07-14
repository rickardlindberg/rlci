from rlci.events import Events
from rlci.infrastructure import Terminal, Process

class Engine:

    """
    I am the engine that runs pipelines.

    I can trigger a pre-defined pipeline:

    >>> db = DB.create_in_memory()
    >>> db.save_pipeline(rlci_pipeline())
    >>> events = Events()
    >>> terminal = events.listen(Terminal.create_null())
    >>> process = events.listen(Process.create_null(responses={
    ...    ('mktemp', '-d'): [
    ...        {"output": ["/tmp/workspace"]}
    ...    ],
    ...    tuple(ProcessInDirectory.create_command(['git', 'rev-parse', 'HEAD'], '/tmp/workspace')): [
    ...        {"output": ["<git-commit>"]}
    ...    ],
    ... }))
    >>> Engine(terminal=terminal, process=process, db=db).trigger()
    True
    >>> events # doctest: +ELLIPSIS
    STDOUT => 'Triggered RLCIPipeline'
    STDOUT => "['mktemp', '-d']"
    PROCESS => ['mktemp', '-d']
    STDOUT => '/tmp/workspace'
    STDOUT => "[..., 'git', 'clone', 'git@github.com:rickardlindberg/rlci.git', '.']"
    PROCESS => [..., 'git', 'clone', 'git@github.com:rickardlindberg/rlci.git', '.']
    STDOUT => "[..., 'git', 'merge', '--no-ff', '-m', 'Integrate.', 'origin/BRANCH']"
    PROCESS => [..., 'git', 'merge', '--no-ff', '-m', 'Integrate.', 'origin/BRANCH']
    STDOUT => "[..., './zero.py', 'build']"
    PROCESS => [..., './zero.py', 'build']
    STDOUT => "[..., 'git', 'push']"
    PROCESS => [..., 'git', 'push']
    STDOUT => "[..., 'git', 'rev-parse', 'HEAD']"
    PROCESS => [..., 'git', 'rev-parse', 'HEAD']
    STDOUT => '<git-commit>'
    STDOUT => "[..., './zero.py', 'deploy', '<git-commit>']"
    PROCESS => [..., './zero.py', 'deploy', '<git-commit>']
    STDOUT => "['rm', '-rf', '/tmp/workspace']"
    PROCESS => ['rm', '-rf', '/tmp/workspace']

    Pipeline is aborted if process fails:

    >>> db = DB.create_in_memory()
    >>> db.save_pipeline(rlci_pipeline())
    >>> events = Events()
    >>> terminal = events.listen(Terminal.create_null())
    >>> process = events.listen(Process.create_null(responses={
    ...    ('mktemp', '-d'): [
    ...        {"returncode": 1}
    ...    ],
    ... }))
    >>> Engine(terminal=terminal, process=process, db=db).trigger()
    False
    >>> events
    STDOUT => 'Triggered RLCIPipeline'
    STDOUT => "['mktemp', '-d']"
    PROCESS => ['mktemp', '-d']
    STDOUT => 'FAIL'
    """

    def __init__(self, terminal, process, db):
        self.terminal = terminal
        self.process = process
        self.db = db

    def trigger(self):
        try:
            pipeline = self.db.get_pipeline()
            self.terminal.print_line(f"Triggered {pipeline['name']}")
            execution_id = self.db.create_execution()
            with Workspace(PipelineStageProcess(self.terminal, self.process, self.db, execution_id)) as workspace:
                variables = {}
                for step in pipeline["steps"]:
                    command = [
                        x if isinstance(x, str) else variables[x["variable"]]
                        for x
                        in step["command"]
                    ]
                    if step.get("variable") is None:
                        workspace.run(command)
                    else:
                        output = []
                        workspace.run(command, output.append)
                        variables[step["variable"]] = " ".join(output)
                return True
        except CommandFailure:
            self.terminal.print_line(f"FAIL")
            return False


def rlci_pipeline():
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

class DB:

    def __init__(self, document_store):
        self.document_store = document_store

    def save_pipeline(self, pipeline):
        self.document_store.create({
            "executions": [],
            "definition": pipeline
        }, "default-pipeline")

    def get_pipeline(self):
        return self.document_store.get("default-pipeline")["definition"]

    def get_execution(self, execution_id):
        return self.document_store.get(execution_id)

    def create_execution(self):
        execution_id = self.document_store.create([])
        self.document_store.modify(
            "default-pipeline",
            lambda x: x["executions"].append(execution_id)
        )
        return execution_id

    def create_output(self, command):
        return self.document_store.create({"command": command, "returncode": None, "lines": []})

    def add_output_line(self, output_id, line):
        self.document_store.modify(
            output_id,
            lambda x: x["lines"].append(line)
        )

    def set_ouput_code(self, output_id, returncode):
        self.document_store.modify(
            output_id,
            lambda x: x.__setitem__("returncode", returncode)
        )

    def add_output(self, execution_id, output_id):
        self.document_store.modify(
            execution_id,
            lambda x: x.append(output_id)
        )

    @staticmethod
    def create():
        return DB.create_in_memory()

    @staticmethod
    def create_in_memory():
        return DB(document_store=InMemoryDocumentStore())

class InMemoryDocumentStore:

    def __init__(self):
        self.documents = {}

    def create(self, data, name=None):
        if name is None:
            document_id = f"id_{len(self.documents)}"
        else:
            document_id = name
        self.documents[document_id] = data
        return document_id

    def get(self, document_id):
        return self.documents[document_id]

    def modify(self, document_id, fn):
        fn(self.documents[document_id])

class Workspace:

    def __init__(self, process):
        self.process = process

    def __enter__(self):
        output = []
        self.process.run(["mktemp", "-d"], output=output.append)
        self.workspace = "".join(output)
        return ProcessInDirectory(self.process, self.workspace)

    def __exit__(self, type, value, traceback):
        self.process.run(["rm", "-rf", self.workspace])

class ProcessInDirectory:

    """
    I execute a command in a directory:

    >>> events = Events()
    >>> process = events.listen(Process.create_null())
    >>> ProcessInDirectory(process, "/tmp/foo").run(["ls"])
    >>> events
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/tmp/foo', 'ls']
    """

    def __init__(self, process, directory):
        self.process = process
        self.directory = directory

    def run(self, command, output=lambda x: None):
        self.process.run(self.create_command(command, self.directory), output)

    @staticmethod
    def create_command(command, directory):
        return [
            "python3",
            "-c",
            "; ".join([
                "import sys",
                "import os",
                "os.chdir(sys.argv[1])",
                "os.execvp(sys.argv[2], sys.argv[2:])",
            ]),
            directory
        ] + command

class PipelineStageProcess:

    def __init__(self, terminal, process, db, execution_id):
        self.terminal = terminal
        self.process = process
        self.db = db
        self.execution_id = execution_id

    def run(self, command, output=lambda x: None):
        def log(line):
            self.terminal.print_line(line)
            output(line)
            self.db.add_output_line(output_id, line)
        output_id = self.db.create_output(command)
        self.terminal.print_line(repr(command))
        returncode = self.process.run(command, output=log)
        self.db.set_ouput_code(output_id, returncode)
        self.db.add_output(self.execution_id, output_id)
        if returncode != 0:
            raise CommandFailure()

class CommandFailure(Exception):
    pass
