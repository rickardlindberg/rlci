from rlci.events import Events
from rlci.infrastructure import Terminal, Process

class Engine:

    """
    I am the engine that runs pipelines.

    ## Stage execution

    I log an execution:

    >>> Engine.trigger_in_test_mode(
    ...     {"name": "TEST", "steps": [{"command": ["ls"]}]},
    ...     responses={
    ...         tuple(Workspace.create_create_command()): [
    ...             {"output": ["/tmp/workspace"]}
    ...         ],
    ...     }
    ... )["events"].filter("STDOUT") # doctest: +ELLIPSIS
    STDOUT => 'Triggered TEST'
    STDOUT => "['mktemp', '-d']"
    STDOUT => '/tmp/workspace'
    STDOUT => "[..., 'ls']"
    STDOUT => "['rm', '-rf', '/tmp/workspace']"

    ### Success

    >>> trigger = Engine.trigger_in_test_mode(
    ...     {"name": "TEST", "steps": []}
    ... )

    I return True:

    >>> trigger["successful"]
    True

    I don't log a failure message:

    >>> trigger["events"].has("STDOUT", "FAIL")
    False

    ### Failure

    >>> trigger = Engine.trigger_in_test_mode(
    ...     {"name": "TEST"},
    ...     responses={
    ...         tuple(Workspace.create_create_command()): [
    ...             {"returncode": 1}
    ...         ],
    ...     }
    ... )

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
            with Workspace(PipelineStageProcess(self.terminal, self.process)) as workspace:
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

    @staticmethod
    def trigger_in_test_mode(pipeline, responses={}):
        db = DB.create()
        db.save_pipeline("test", pipeline)
        events = Events()
        terminal = events.listen(Terminal.create_null())
        process = events.listen(Process.create_null(responses=responses))
        successful = Engine(terminal=terminal, process=process, db=db).trigger("test")
        return {"successful": successful, "events": events}

class DB:

    def __init__(self):
        self.pipelines = {}

    def save_pipeline(self, name, pipeline):
        self.pipelines[name] = pipeline

    def get_pipeline(self, name):
        return self.pipelines[name]

    @staticmethod
    def create():
        return DB()

class Workspace:

    def __init__(self, process):
        self.process = process

    def __enter__(self):
        output = []
        self.process.run(self.create_create_command(), output=output.append)
        self.workspace = "".join(output)
        return ProcessInDirectory(self.process, self.workspace)

    def __exit__(self, type, value, traceback):
        self.process.run(["rm", "-rf", self.workspace])

    @staticmethod
    def create_create_command():
        return ["mktemp", "-d"]

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

    def __init__(self, terminal, process):
        self.terminal = terminal
        self.process = process

    def run(self, command, output=lambda x: None):
        def log(line):
            self.terminal.print_line(line)
            output(line)
        self.terminal.print_line(repr(command))
        returncode = self.process.run(command, output=log)
        if returncode != 0:
            raise CommandFailure()

class CommandFailure(Exception):
    pass
