from rlci.events import Events
from rlci.infrastructure import Terminal, Process

class Engine:

    """
    I am the engine that runs pipelines.

    >>> TEST_PIPELINE = {"name": "TEST", "steps": []}

    Triggering
    ==========

    I log which pipeline I triggered:

    >>> trigger = Engine.trigger_in_test_mode(TEST_PIPELINE)
    >>> trigger["events"].has("STDOUT", "Triggered TEST")
    True

    Pipeline succeeds
    -----------------

    >>> trigger = Engine.trigger_in_test_mode(TEST_PIPELINE)

    I return True:

    >>> trigger["successful"]
    True

    I don't log a failure message:

    >>> trigger["events"].has("STDOUT", "FAIL")
    False

    Pipeline fails
    --------------

    >>> trigger = Engine.trigger_in_test_mode(TEST_PIPELINE, simulate_failure=True)

    I return False:

    >>> trigger["successful"]
    False

    I log a failure message:

    >>> trigger["events"].has("STDOUT", "FAIL")
    True
    """

    def __init__(self, terminal, process, db):
        self.terminal = terminal
        self.process = process
        self.db = db

    def trigger(self, name):
        pipeline = self.db.get_pipeline(name)
        self.terminal.print_line(f"Triggered {pipeline['name']}")
        try:
            StageExecution(terminal=self.terminal, process=self.process).run(pipeline)
            return True
        except CommandFailure:
            self.terminal.print_line(f"FAIL")
            return False

    @staticmethod
    def trigger_in_test_mode(pipeline, simulate_failure=False, process_responses={}):
        db = DB.create_in_memory()
        db.save_pipeline("test", pipeline)
        events = Events()
        terminal = events.listen(Terminal.create_null())
        if simulate_failure:
            process_responses = {
                tuple(Workspace.create_create_command()): [
                    {"returncode": 99}
                ]
            }
        process = events.listen(Process.create_null(responses=process_responses))
        successful = Engine(terminal=terminal, process=process, db=db).trigger("test")
        return {"successful": successful, "events": events}

class StageExecution:

    """
    I execute a single stage in a pipeline.

    >>> BUILD_DEPLOY_STAGE = {
    ...     "steps": [
    ...         {"command": ["./build"]},
    ...         {"command": ["./deploy"]}
    ...     ]
    ... }

    Workspace isolation
    ===================

    I execute the steps in an isolated workspace:

    >>> StageExecution.run_in_test_mode(BUILD_DEPLOY_STAGE, process_responses={
    ...     tuple(Workspace.create_create_command()): [
    ...         {"output": ["/workspace"]}
    ...     ]
    ... }).filter("PROCESS", "EXCEPTION")
    PROCESS => ['mktemp', '-d']
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/workspace', './build']
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/workspace', './deploy']
    PROCESS => ['rm', '-rf', '/workspace']

    If workspace creations fails, I fail:

    >>> StageExecution.run_in_test_mode(BUILD_DEPLOY_STAGE, process_responses={
    ...     tuple(Workspace.create_create_command()): [
    ...         {"output": ["/workspace"], "returncode": 99}
    ...     ],
    ... }).filter("PROCESS", "EXCEPTION")
    PROCESS => ['mktemp', '-d']
    EXCEPTION => 'CommandFailure'

    If a step fails, I fail, but still clean up the workspace:

    >>> StageExecution.run_in_test_mode(BUILD_DEPLOY_STAGE, process_responses={
    ...     tuple(Workspace.create_create_command()): [
    ...         {"output": ["/workspace"]}
    ...     ],
    ...     tuple(ProcessInDirectory.create_command(["./build"], "/workspace")): [
    ...         {"returncode": 99}
    ...     ]
    ... }).filter("PROCESS", "EXCEPTION")
    PROCESS => ['mktemp', '-d']
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/workspace', './build']
    PROCESS => ['rm', '-rf', '/workspace']
    EXCEPTION => 'CommandFailure'

    Logging
    =======

    I log the commands I run:

    >>> StageExecution.run_in_test_mode(BUILD_DEPLOY_STAGE, process_responses={
    ...     tuple(Workspace.create_create_command()): [
    ...         {"output": ["/workspace"]}
    ...     ]
    ... }).filter("STDOUT")
    STDOUT => "['mktemp', '-d']"
    STDOUT => '/workspace'
    STDOUT => "['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/workspace', './build']"
    STDOUT => "['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/workspace', './deploy']"
    STDOUT => "['rm', '-rf', '/workspace']"

    Command interpretation
    ======================

    I can capture output from commands and use that in later commands:

    >>> StageExecution.run_in_test_mode({
    ...     "steps": [
    ...         {"command": ["cat", "path.txt"], "variable": "path"},
    ...         {"command": ["cd", {"variable": "path"}]},
    ...     ]
    ... }, process_responses={
    ...     tuple(ProcessInDirectory.create_command(["cat", "path.txt"], "")): [
    ...         {"output": ["secret-path"]}
    ...     ]
    ... }).filter("PROCESS") # doctest: +ELLIPSIS
    PROCESS => [...]
    PROCESS => [..., 'cat', 'path.txt']
    PROCESS => [..., 'cd', 'secret-path']
    PROCESS => [...]
    """

    def __init__(self, terminal, process):
        self.terminal = terminal
        self.process = process

    def run(self, stage):
        with Workspace(PipelineStageProcess(self.terminal, self.process)) as workspace:
            variables = {}
            for step in stage["steps"]:
                command = [
                    x if isinstance(x, str) else variables[x["variable"]]
                    for x
                    in step["command"]
                ]
                if step.get("variable") is None:
                    workspace.run(command)
                else:
                    variables[step["variable"]] = workspace.slurp(command)

    @staticmethod
    def run_in_test_mode(stage, process_responses={}):
        events = Events()
        terminal = events.listen(Terminal.create_null())
        process = events.listen(Process.create_null(responses=process_responses))
        try:
            StageExecution(terminal=terminal, process=process).run(stage)
        except CommandFailure:
            events.append(("EXCEPTION", "CommandFailure"))
        return events

class DB:

    def __init__(self):
        self.pipelines = {}

    def save_pipeline(self, name, pipeline):
        self.pipelines[name] = pipeline

    def get_pipeline(self, name):
        return self.pipelines[name]

    @staticmethod
    def create():
        return DB.create_in_memory()

    @staticmethod
    def create_in_memory():
        return DB()

class Workspace:

    def __init__(self, process):
        self.process = process

    def __enter__(self):
        self.workspace = self.process.slurp(self.create_create_command())
        return ProcessInDirectory(self.process, self.workspace)

    def __exit__(self, type, value, traceback):
        self.process.run(["rm", "-rf", self.workspace])

    @staticmethod
    def create_create_command():
        return ["mktemp", "-d"]

class SlurpMixin:

    def slurp(self, command):
        output = []
        self.run(command, output=output.append)
        return "".join(output)

class ProcessInDirectory(SlurpMixin):

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

class PipelineStageProcess(SlurpMixin):

    def __init__(self, terminal, process):
        self.terminal = terminal
        self.process = process

    def run(self, command, output=lambda x: None):
        def log(line):
            self.terminal.print_line(line)
            output(line)
        self.terminal.print_line(repr(command))
        if self.process.run(command, output=log) != 0:
            raise CommandFailure()

def slurp(process, command):
    output = []
    process.run(command, output=output.append)
    return "".join(output)

class CommandFailure(Exception):
    pass
