#!/usr/bin/env python3

import doctest
import sys
import subprocess
import unittest

class ZeroApp:

    """
    Prints usage:

    >>> ZeroApp.run_in_test_mode(args=[])
    STDOUT => 'I am a tool for zero friction development'

    Runs tests:

    >>> ZeroApp.run_in_test_mode(args=['build'])
    DOCTEST_MODULE => 'zero'
    TEST_RUN => None
    """

    def __init__(self, args=None, terminal=None, tests=None):
        self.args = Args() if args is None else args
        self.terminal = Terminal() if terminal is None else terminal
        self.tests = Tests() if tests is None else tests

    def run(self):
        if self.args.get() == ["build"]:
            self.tests.add_doctest("zero")
            self.tests.run()
        else:
            self.terminal.print_line("I am a tool for zero friction development")

    @staticmethod
    def run_in_test_mode(args=[]):
        events = EventCollector()
        args = Args.create_null(args)
        terminal = Terminal.create_null()
        terminal.listen(events)
        tests = Tests.create_null()
        tests.listen(events)
        app = ZeroApp(args=args, terminal=terminal, tests=tests)
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

class Tests(Observable):

    """
    Wrapper for Python's unittest/doctest.

    >>> tests = Tests()
    >>> tests.add_doctest("doctest_testmodule")
    >>> tests.run()
    (True, 1)

    Logs its actions:

    >>> events = EventCollector()
    >>> tests = Tests.create_null()
    >>> tests.listen(events)
    >>> tests.add_doctest("doctest_testmodule")
    >>> tests.run()
    (True, 0)
    >>> events
    DOCTEST_MODULE => 'doctest_testmodule'
    TEST_RUN => None
    """

    def __init__(self, unittest=unittest, doctest=doctest):
        Observable.__init__(self)
        self.unittest = unittest
        self.doctest = doctest
        self.suite = unittest.TestSuite()

    def add_doctest(self, module_name):
        self.notify("DOCTEST_MODULE", module_name)
        self.suite.addTest(self.doctest.DocTestSuite(__import__(module_name)))

    def run(self):
        self.notify("TEST_RUN", None)
        result = self.unittest.TextTestRunner().run(self.suite)
        return (result.wasSuccessful(), result.testsRun)

    @staticmethod
    def create_null():
        class NullUnittest:
            def TestSuite(self):
                return NullTestSuite()
            def TextTestRunner(self):
                return NullTextTestRunner()
        class NullTextTestRunner:
            def run(self, suite):
                return NullResult()
        class NullResult:
            testsRun = 0
            def wasSuccessful(self):
                return True
        class NullTestSuite:
            def addTest(self, test):
                pass
        class NullDoctest:
            def DocTestSuite(self, module):
                pass
        return Tests(unittest=NullUnittest(), doctest=NullDoctest())

class Args:

    """
    >>> subprocess.run([
    ...     "python", "-c"
    ...     "import zero; print(zero.Args().get())",
    ...     "arg1", "arg2"
    ... ], stdout=subprocess.PIPE).stdout
    b"['arg1', 'arg2']\\n"

    >>> Args.create_null(["one", "two"]).get()
    ['one', 'two']
    """

    def __init__(self, sys=sys):
        self.sys = sys

    def get(self):
        return self.sys.argv[1:]

    @staticmethod
    def create_null(args):
        class NullSys:
            argv = [None]+args
        return Args(NullSys())

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
    ZeroApp().run()
