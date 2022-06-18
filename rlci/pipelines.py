import subprocess

from rlci.events import Observable, Events

class PipelineRuntime(Observable):

    """
    I can run shell commands:

    >>> PipelineRuntime().sh('echo hello')
    b'hello\\n'

    I fail if command fails:

    >>> PipelineRuntime().sh('exit 1')
    Traceback (most recent call last):
        ...
    subprocess.CalledProcessError: Command 'exit 1' returned non-zero exit status 1.

    The null version of me, runs no shell commands:

    >>> PipelineRuntime.create_null().sh('echo hello')
    b''

    I log commands:

    >>> events = Events()
    >>> pipeline = PipelineRuntime.create_null()
    >>> pipeline.register_event_listener(events)
    >>> _ = pipeline.sh("echo hello")
    >>> events
    SH => 'echo hello'
    """

    def __init__(self, subprocess=subprocess):
        Observable.__init__(self)
        self.subprocess = subprocess

    def sh(self, command):
        self.notify("SH", command)
        return self.subprocess.run(command, shell=True,
        stdout=self.subprocess.PIPE, check=True).stdout

    @staticmethod
    def create_null():
        class NullSubprocess:
            PIPE = None
            def run(self, *args, **kwargs):
                return NullResponse()
        class NullResponse:
            stdout = b''
        return PipelineRuntime(NullSubprocess())

class Pipeline:

    def __init__(self, runtime):
        self.runtime = runtime

    @staticmethod
    def run_in_test_mode():
        events = Events()
        runtime = PipelineRuntime.create_null()
        runtime.register_event_listener(events)
        pipeline = RLCIPipeline(runtime)
        pipeline.run()
        return events

class RLCIPipeline(Pipeline):

    """
    >>> RLCIPipeline.run_in_test_mode()
    SH => 'git clone git@github.com:rickardlindberg/rlci.git .'
    SH => 'git merge --no-ff -m "Integrate." origin/BRANCH'
    SH => './zero.py build'
    SH => 'git push'
    """

    def run(self):
        self.runtime.sh("git clone git@github.com:rickardlindberg/rlci.git .")
        self.runtime.sh("git merge --no-ff -m \"Integrate.\" origin/BRANCH")
        self.runtime.sh("./zero.py build")
        self.runtime.sh("git push")

class Engine(Observable):

    """
    I am the engine that runs pipelines.

    I can trigger a pipeline:

    >>> engine_events = Events()
    >>> runtime_events = Events()
    >>> runtime = PipelineRuntime.create_null()
    >>> runtime.register_event_listener(runtime_events)
    >>> engine = Engine(runtime=runtime)
    >>> engine.register_event_listener(engine_events)
    >>> engine.trigger("RLCIPipeline")
    >>> engine_events
    TRIGGER => 'RLCIPipeline'
    >>> runtime_events == RLCIPipeline.run_in_test_mode()
    True
    """

    def __init__(self, runtime=None):
        Observable.__init__(self)
        self.pipelines = {
            "RLCIPipeline": RLCIPipeline,
        }
        self.runtime = PipelineRuntime() if runtime is None else runtime

    def trigger(self, name):
        self.notify("TRIGGER", name)
        self.pipelines[name](self.runtime).run()
