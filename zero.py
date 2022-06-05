#!/usr/bin/env python3

import doctest
import subprocess
import sys
import unittest

from rlci import Events, Terminal, Observable

class ZeroApp:

    """
    I am a tool for zero friction development.

    I print usage when run with no arguments:

    >>> ZeroApp.run_in_test_mode(args=[])
    STDOUT => 'I am a tool for zero friction development'

    I run tests when run with the 'build' argument:

    >>> ZeroApp.run_in_test_mode(args=['build'])
    DOCTEST_MODULE => 'zero'
    DOCTEST_MODULE => 'rlci'
    TEST_RUN => None
    """

    def __init__(self, args=None, terminal=None, tests=None):
        self.args = Args() if args is None else args
        self.terminal = Terminal() if terminal is None else terminal
        self.tests = Tests() if tests is None else tests

    def run(self):
        if self.args.get() == ["build"]:
            self.tests.add_doctest("zero")
            self.tests.add_doctest("rlci")
            self.tests.run()
        else:
            self.terminal.print_line("I am a tool for zero friction development")

    @staticmethod
    def run_in_test_mode(args=[]):
        events = Events()
        args = Args.create_null(args)
        terminal = Terminal.create_null()
        terminal.register_event_listener(events)
        tests = Tests.create_null()
        tests.register_event_listener(events)
        app = ZeroApp(args=args, terminal=terminal, tests=tests)
        app.run()
        return events

class Tests(Observable):

    """
    I am a infrastructure wrapper for Python's test modules.

    I run doctests and return success/number of tests run:

    >>> tests = Tests()
    >>> tests.add_doctest("doctest_testmodule")
    >>> tests.run()
    (True, 1)

    The null version of me runs no tests for real:

    >>> tests = Tests.create_null()
    >>> tests.add_doctest("doctest_testmodule")
    >>> tests.run()
    (True, 0)

    I log my actions (tested using null version):

    >>> events = Events()
    >>> tests = Tests.create_null()
    >>> tests.register_event_listener(events)
    >>> tests.add_doctest("doctest_testmodule")
    >>> _ = tests.run()
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
    I am an infrastructure wrapper for reading program arguments (via the sys
    module).

    I return the arguments passed to the program:

    >>> subprocess.run([
    ...     "python", "-c",
    ...     "import zero; print(zero.Args().get())",
    ...     "arg1", "arg2"
    ... ], stdout=subprocess.PIPE, check=True).stdout
    b"['arg1', 'arg2']\\n"

    The null version of me does not read arguments passed to the program, but
    instead return configured arguments:

    >>> subprocess.run([
    ...     "python", "-c",
    ...     "import zero; print(zero.Args.create_null(['configured1']).get())",
    ...     "arg1", "arg2"
    ... ], stdout=subprocess.PIPE, check=True).stdout
    b"['configured1']\\n"
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

if __name__ == "__main__":
    ZeroApp().run()
