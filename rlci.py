import subprocess
import sys

class RLCIApp:

    """
    I am a tool to facilitate CI/CD.

    I run a predefined pipeline:

    >>> RLCIApp.run_in_test_mode()
    STDOUT => 'pipeline run OK'
    """

    def __init__(self, terminal=None):
        self.terminal = Terminal() if terminal is None else terminal

    def run(self):
        self.terminal.print_line("pipeline run OK")

    @staticmethod
    def run_in_test_mode():
        events = Events()
        terminal = Terminal.create_null()
        terminal.register_event_listener(events)
        app = RLCIApp(terminal=terminal)
        app.run()
        return events

class Events(list):

    def notify(self, event, data):
        self.append((event, data))

    def filter(self, event):
        return Events(x for x in self if x[0] == event)

    def __repr__(self):
        return "\n".join(f"{event} => {repr(data)}" for event, data in self)

class Observable:

    def __init__(self):
        self.event_listeners = []

    def register_event_listener(self, event_listener):
        self.event_listeners.append(event_listener)

    def notify(self, event, data):
        for event_listener in self.event_listeners:
            event_listener.notify(event, data)

class Terminal(Observable):

    """
    I represent a terminal emulator to which text can be printed.

    I write text to stdout:

    >>> subprocess.run([
    ...     "python", "-c",
    ...     "import rlci; rlci.Terminal().print_line('hello')"
    ... ], stdout=subprocess.PIPE, check=True).stdout
    b'hello\\n'

    The null version of me doesn't write anything to stdout:

    >>> subprocess.run([
    ...     "python", "-c",
    ...     "import rlci; rlci.Terminal.create_null().print_line('hello')"
    ... ], stdout=subprocess.PIPE, check=True).stdout
    b''

    I log the lines that I print:

    >>> events = Events()
    >>> terminal = Terminal.create_null()
    >>> terminal.register_event_listener(events)
    >>> terminal.print_line("hello")
    >>> events
    STDOUT => 'hello'
    """

    def __init__(self, stdout=sys.stdout):
        Observable.__init__(self)
        self.stdout = stdout

    def print_line(self, text):
        self.notify("STDOUT", text)
        self.stdout.write(text)
        self.stdout.write("\n")
        self.stdout.flush()

    @staticmethod
    def create_null():
        class NullStream:
            def write(self, text):
                pass
            def flush(self):
                pass
        return Terminal(NullStream())

if __name__ == "__main__":
    RLCIApp().run()
