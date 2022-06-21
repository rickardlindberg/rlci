import contextlib
import os
import subprocess
import tempfile

from rlci.events import Observable, Events
from rlci.infrastructure import Terminal

class Runtime(Observable):

    """
    ## Shell commands

    I can run shell commands:

    >>> Runtime().sh('echo hello')
    b'hello\\n'

    I fail if command fails:

    >>> Runtime().sh('exit 1')
    Traceback (most recent call last):
        ...
    subprocess.CalledProcessError: Command 'exit 1' returned non-zero exit status 1.

    The null version of me, runs no shell commands:

    >>> Runtime.create_null().sh('echo hello')
    b''

    I log commands:

    >>> events = Events()
    >>> pipeline = Runtime.create_null()
    >>> pipeline.register_event_listener(events)
    >>> _ = pipeline.sh("echo hello")
    >>> events
    SH => 'echo hello'

    ## Workspace commands

    I can create empty workspaces:

    >>> events = Events()
    >>> runtime = Runtime()
    >>> runtime.register_event_listener(events)
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

    def sh(self, command):
        self.notify("SH", command)
        return self.subprocess.run(command, shell=True,
        stdout=self.subprocess.PIPE, check=True).stdout

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

class Pipeline:

    def __init__(self, runtime):
        self.runtime = runtime

    @staticmethod
    def run_in_test_mode():
        events = Events()
        runtime = Runtime.create_null()
        runtime.register_event_listener(events)
        pipeline = RLCIPipeline(runtime)
        pipeline.run()
        return events

class RLCIPipeline(Pipeline):

    """
    >>> RLCIPipeline.run_in_test_mode()
    EMPTY_WORKSPACE => 'create'
    SH => 'git clone git@github.com:rickardlindberg/rlci.git .'
    SH => 'git merge --no-ff -m "Integrate." origin/BRANCH'
    SH => './zero.py build'
    SH => 'git push'
    EMPTY_WORKSPACE => 'delete'
    """

    def run(self):
        with self.runtime.workspace():
            self.runtime.sh("git clone git@github.com:rickardlindberg/rlci.git .")
            self.runtime.sh("git merge --no-ff -m \"Integrate.\" origin/BRANCH")
            self.runtime.sh("./zero.py build")
            self.runtime.sh("git push")

class Engine:

    """
    I am the engine that runs pipelines.

    I can trigger a pre-defined pipeline:

    >>> runtime_events = Events()
    >>> runtime = Runtime.create_null()
    >>> runtime.register_event_listener(runtime_events)
    >>> engine = Engine(runtime=runtime, terminal=Terminal.create_null())
    >>> engine.trigger("RLCIPipeline")
    >>> runtime_events == RLCIPipeline.run_in_test_mode()
    True

    I notify which pipeline I triggered:

    >>> events = Events()
    >>> terminal = Terminal.create_null()
    >>> terminal.register_event_listener(events)
    >>> engine = Engine(runtime=Runtime.create_null(), terminal=terminal)
    >>> engine.trigger("RLCIPipeline")
    >>> events
    STDOUT => 'Triggered RLCIPipeline'
    """

    def __init__(self, runtime=None, terminal=None):
        self.pipelines = {
            "RLCIPipeline": RLCIPipeline,
        }
        self.runtime = Runtime() if runtime is None else runtime
        self.terminal = Terminal() if terminal is None else terminal

    def trigger(self, name):
        self.pipelines[name](self.runtime).run()
        self.terminal.print_line(f"Triggered {name}")
