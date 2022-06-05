#!/usr/bin/env python3

import doctest
import sys
import subprocess

class ZeroApp:

    """
    >>> ZeroApp.run_in_test_mode(args=[])
    STDOUT => 'I am a tool for zero friction development'
    """

    def __init__(self, terminal):
        self.terminal = terminal

    def run(self):
        self.terminal.print_line("I am a tool for zero friction development")

    @staticmethod
    def run_in_test_mode(args=[]):
        events = EventCollector()
        terminal = Terminal.create_null()
        terminal.listen(events)
        app = ZeroApp(terminal=terminal)
        app.run()
        return events

class Observable:

    def __init__(self):
        self.event_listeners = []

    def listen(self, event_listener):
        self.event_listeners.append(event_listener)

    def notify(self, event, text):
        for event_listener in self.event_listeners:
            event_listener.notify(event, text)

class Terminal(Observable):

    """
    Writes to stdout:

    >>> subprocess.run([
    ...     "python", "-c"
    ...     "import zero; zero.Terminal().print_line('hello')"
    ... ], stdout=subprocess.PIPE).stdout
    b'hello\\n'

    Logs printed lines:

    >>> events = EventCollector()
    >>> terminal = Terminal.create_null()
    >>> terminal.listen(events)
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

class EventCollector(list):

    def notify(self, event, text):
        self.append((event, text))

    def __repr__(self):
        return "\n".join(f"{event} => {repr(text)}" for event, text in self)

if __name__ == "__main__":
    #ZeroApp().run()
    doctest.testmod()
    print("OK")
