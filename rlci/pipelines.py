import pprint

from rlci.events import Events
from rlci.infrastructure import Terminal, Process, Filesystem, UnixDomainSocketServer

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

    I write a report of the pipeline run:

    >>> trigger = Engine.trigger_in_test_mode(TEST_PIPELINE)
    >>> report = trigger["filesystem"].read("/opt/rlci/html/index.html")
    >>> "test" in report
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

    def __init__(self, terminal, process, db, filesystem):
        self.terminal = terminal
        self.process = process
        self.db = db
        self.filesystem = filesystem
        self.db.save_pipeline("rlci", rlci_pipeline())
        self.db.save_pipeline("test-pipeline", {"name": "TEST-PIPELINE", "steps": []})

    def trigger(self, name):
        pipeline = self.db.get_pipeline(name)
        self.terminal.print_line(f"Triggered {pipeline['name']}")
        try:
            StageExecution(
                terminal=self.terminal,
                process=self.process,
                db=self.db
            ).run(pipeline)
            return True
        except CommandFailure:
            self.terminal.print_line(f"FAIL")
            return False
        finally:
            report = []
            report.append(f"<h1>Last run pipeline: {name}</h1>")
            for stage_command in self.db.get_stage_commands():
                report.append(f"<h2><pre>{stage_command['command']}<pre></h2>")
                report.append(f"<p><b>returncode: {stage_command['returncode']}</b></p>")
                report.append("<pre>")
                for line in stage_command["output"]:
                    report.append(line)
                report.append("</pre>")
            self.filesystem.write("/opt/rlci/html/index.html", "\n".join(report))

    @staticmethod
    def trigger_in_test_mode(pipeline, simulate_failure=False, process_responses=[]):
        db = DB.create_in_memory()
        db.save_pipeline("test", pipeline)
        events = Events()
        terminal = events.listen(Terminal.create_null())
        filesystem = Filesystem.create_in_memory()
        if simulate_failure:
            process_responses.append({
                "command": Workspace.create_create_command(),
                "returncode": 99,
            })
        process = events.listen(Process.create_null(responses=process_responses))
        engine = Engine(
            terminal=terminal,
            process=process,
            db=db,
            filesystem=filesystem
        )
        server = UnixDomainSocketServer.create_null(simulate_request=b'test')
        engine_server = EngineServer(engine=engine, server=server)
        engine_server.start()
        successful = engine_server.successful
        return {
            "successful": successful,
            "events": events,
            "filesystem": filesystem
        }

class EngineServer:

    def __init__(self, engine, server):
        self.engine = engine
        self.server = server
        self.server.register_handler(self.handle_request)

    def start(self):
        self.server.start("/tmp/rlci-engine.socket")

    def handle_request(self, request):
        self.successful = self.engine.trigger(request.decode('ascii'))
        return str(self.successful).encode('ascii')

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

    >>> StageExecution.run_in_test_mode(BUILD_DEPLOY_STAGE, process_responses=[
    ...     {
    ...         "command": Workspace.create_create_command(),
    ...         "output": ["/workspace"],
    ...     },
    ... ]).filter("PROCESS", "EXCEPTION")
    PROCESS => ['mktemp', '-d']
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/workspace', './build']
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/workspace', './deploy']
    PROCESS => ['rm', '-rf', '/workspace']

    If workspace creations fails, I fail:

    >>> StageExecution.run_in_test_mode(BUILD_DEPLOY_STAGE, process_responses=[
    ...     {
    ...         "command": Workspace.create_create_command(),
    ...         "returncode": 99,
    ...     },
    ... ]).filter("PROCESS", "EXCEPTION")
    PROCESS => ['mktemp', '-d']
    EXCEPTION => 'CommandFailure'

    If a step fails, I fail, but still clean up the workspace:

    >>> StageExecution.run_in_test_mode(BUILD_DEPLOY_STAGE, process_responses=[
    ...     {
    ...         "command": Workspace.create_create_command(),
    ...         "output": ["/workspace"],
    ...     },
    ...     {
    ...         "command": ProcessInDirectory.create_command(["./build"], "/workspace"),
    ...         "returncode": 99,
    ...     },
    ... ]).filter("PROCESS", "EXCEPTION")
    PROCESS => ['mktemp', '-d']
    PROCESS => ['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/workspace', './build']
    PROCESS => ['rm', '-rf', '/workspace']
    EXCEPTION => 'CommandFailure'

    Logging
    =======

    I log the commands I run:

    >>> StageExecution.run_in_test_mode(BUILD_DEPLOY_STAGE, process_responses=[
    ...     {
    ...         "command": Workspace.create_create_command(),
    ...         "output": ["/workspace"],
    ...     },
    ... ]).filter("STDOUT")
    STDOUT => "['mktemp', '-d']"
    STDOUT => '/workspace'
    STDOUT => "['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/workspace', './build']"
    STDOUT => "['python3', '-c', 'import sys; import os; os.chdir(sys.argv[1]); os.execvp(sys.argv[2], sys.argv[2:])', '/workspace', './deploy']"
    STDOUT => "['rm', '-rf', '/workspace']"

    I store logs in the database of the commands I run:

    >>> run = StageExecution.run_in_test_mode(BUILD_DEPLOY_STAGE, process_responses=[
    ...     {
    ...         "command": Workspace.create_create_command(),
    ...         "output": ["/workspace"],
    ...     },
    ...     {
    ...         "command": ProcessInDirectory.create_command(["./build"], "/workspace"),
    ...         "output": ["I failed :("],
    ...         "returncode": 99,
    ...     },
    ... ], return_events=False)
    >>> pprint.pprint(run["db"].get_stage_commands())
    [{'command': ['mktemp', '-d'], 'output': ['/workspace'], 'returncode': 0},
     {'command': ['python3',
                  '-c',
                  'import sys; import os; os.chdir(sys.argv[1]); '
                  'os.execvp(sys.argv[2], sys.argv[2:])',
                  '/workspace',
                  './build'],
      'output': ['I failed :('],
      'returncode': 99},
     {'command': ['rm', '-rf', '/workspace'], 'output': [], 'returncode': 0}]

    Command interpretation
    ======================

    I can capture output from commands and use that in later commands:

    >>> StageExecution.run_in_test_mode({
    ...     "steps": [
    ...         {"command": ["cat", "path.txt"], "variable": "path"},
    ...         {"command": ["cd", {"variable": "path"}]},
    ...     ]
    ... }, process_responses=[
    ...     {
    ...         "command": ProcessInDirectory.create_command(["cat", "path.txt"], ""),
    ...         "output": ["secret-path"],
    ...     },
    ... ]).filter("PROCESS") # doctest: +ELLIPSIS
    PROCESS => [...]
    PROCESS => [..., 'cat', 'path.txt']
    PROCESS => [..., 'cd', 'secret-path']
    PROCESS => [...]
    """

    def __init__(self, terminal, process, db):
        self.terminal = terminal
        self.process = process
        self.db = db

    def run(self, stage):
        self.db.create_stage_commands()
        with Workspace(PipelineStageProcess(self.terminal, self.process, self.db)) as workspace:
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
    def run_in_test_mode(stage, process_responses=[], return_events=True):
        events = Events()
        terminal = events.listen(Terminal.create_null())
        process = events.listen(Process.create_null(responses=process_responses))
        db = DB.create_in_memory()
        try:
            StageExecution(terminal=terminal, process=process, db=db).run(stage)
        except CommandFailure:
            events.append(("EXCEPTION", "CommandFailure"))
        if return_events:
            return events
        else:
            return {"db": db}

class DB:

    def __init__(self):
        self.pipelines = {}

    def save_pipeline(self, name, pipeline):
        self.pipelines[name] = pipeline

    def get_pipeline(self, name):
        return self.pipelines[name]

    def create_stage_commands(self):
        self.stage_commands = []

    def get_stage_commands(self):
        return self.stage_commands

    def add_stage_command(self, command):
        self.stage_commands.append({"returncode": None, "output": [], "command": command})

    def set_stage_command_returncode(self, returncode):
        self.stage_commands[-1]["returncode"] = returncode

    def add_stage_command_output(self, line):
        self.stage_commands[-1]["output"].append(line)

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

    def __init__(self, terminal, process, db):
        self.terminal = terminal
        self.process = process
        self.db = db

    def run(self, command, output=lambda x: None):
        def log(line):
            self.terminal.print_line(line)
            self.db.add_stage_command_output(line)
            output(line)
        self.terminal.print_line(repr(command))
        self.db.add_stage_command(command)
        returncode = self.process.run(command, output=log)
        self.db.set_stage_command_returncode(returncode)
        if returncode != 0:
            raise CommandFailure()

class CommandFailure(Exception):
    pass

def rlci_pipeline():
    """
    >>> Engine.trigger_in_test_mode(
    ...     rlci_pipeline(),
    ...     process_responses=[
    ...         {
    ...             "command": Workspace.create_create_command(),
    ...             "output": ["/workspace"],
    ...         },
    ...         {
    ...             "command": ProcessInDirectory.create_command(['git', 'rev-parse', 'HEAD'], '/workspace'),
    ...             "output": ["<git-commit>"],
    ...         },
    ...     ]
    ... )["events"].filter("PROCESS") # doctest: +ELLIPSIS
    PROCESS => ['mktemp', '-d']
    PROCESS => [..., 'git', 'clone', 'git@github.com:rickardlindberg/rlci.git', '.']
    PROCESS => [..., 'git', 'merge', '--no-ff', '-m', 'Integrate.', 'origin/BRANCH']
    PROCESS => [..., './zero.py', 'build']
    PROCESS => [..., 'git', 'push']
    PROCESS => [..., 'git', 'rev-parse', 'HEAD']
    PROCESS => [..., './zero.py', 'deploy', '<git-commit>']
    PROCESS => ['rm', '-rf', '/workspace']
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
