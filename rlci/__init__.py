import sys

from rlci.events import Observable, Events
from rlci.pipelines import Engine, Runtime
from rlci.infrastructure import Args, Terminal

class RLCIApp:

    """
    I am a tool to facilitate CI/CD.

    I can trigger a predefined pipeline:

    >>> RLCIApp.run_in_test_mode(args=["trigger"])
    TRIGGER => 'RLCIPipeline'

    I fail when given other args:

    >>> RLCIApp.run_in_test_mode(args=[])
    STDOUT => 'Usage: python3 rlci.py trigger'
    EXIT => 1
    """

    def __init__(self, terminal=None, args=None, pipeline_engine=None):
        self.terminal = Terminal() if terminal is None else terminal
        self.args = Args() if args is None else args
        self.pipeline_engine = Engine() if pipeline_engine is None else pipeline_engine

    def run(self):
        if self.args.get() == ["trigger"]:
            self.pipeline_engine.trigger("RLCIPipeline")
        else:
            self.terminal.print_line("Usage: python3 rlci.py trigger")
            sys.exit(1)

    @staticmethod
    def run_in_test_mode(args=[]):
        events = Events()
        terminal = Terminal.create_null()
        terminal.register_event_listener(events)
        pipeline_engine = Engine(runtime=Runtime.create_null())
        pipeline_engine.register_event_listener(events)
        app = RLCIApp(
            terminal=terminal,
            args=Args.create_null(args),
            pipeline_engine=pipeline_engine
        )
        try:
            app.run()
        except SystemExit as e:
            events.append(("EXIT", e.code))
        return events
