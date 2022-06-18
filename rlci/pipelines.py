import subprocess

from rlci.events import Observable

class Pipeline(Observable):

    """
    I can run shell commands:

    >>> Pipeline().sh('echo hello')
    b'hello\\n'

    I fail if command fails:

    >>> Pipeline().sh('exit 1')
    Traceback (most recent call last):
        ...
    subprocess.CalledProcessError: Command 'exit 1' returned non-zero exit status 1.

    The null version of me, runs no shell commands:

    >>> Pipeline.create_null().sh('echo hello')
    b''

    I log commands:

    >>> events = Events()
    >>> pipeline = Pipeline.create_null()
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
        return Pipeline(NullSubprocess())

class RLCIPipeline:

    def __init__(self, pipeline):
        self.pipeline = pipeline

    def run(self):
        self.pipeline.sh("git clone git@github.com:rickardlindberg/rlci.git .")
        self.pipeline.sh("git merge --no-ff -m \"Integrate.\" origin/BRANCH")
        self.pipeline.sh("./zero.py build")
        self.pipeline.sh("git push")
