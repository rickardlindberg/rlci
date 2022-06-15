#!/usr/bin/env python3

import doctest
import subprocess
import sys
import unittest

from rlci import Events, Terminal, Observable

class ZeroApp:

    """
    I am a tool for zero friction development.

    ## Usage

    I print usage when run with no arguments:

    >>> ZeroApp.run_in_test_mode(args=[])
    STDOUT => 'I am a tool for zero friction development of RLCI.'
    STDOUT => ''
    STDOUT => 'Run all tests with'
    STDOUT => ''
    STDOUT => '    ./zero.py build'
    EXIT => 1

    ## Building

    I run tests when run with the 'build' argument:

    >>> ZeroApp.run_in_test_mode(args=['build'])
    DOCTEST_MODULE => 'zero'
    DOCTEST_MODULE => 'rlci'
    TEST_RUN => None

    I exit with error code if tests fail:

    >>> ZeroApp.run_in_test_mode(
    ...   args=['build'],
    ...   tests_succeed=False
    ... ).filter("EXIT")
    EXIT => 1

    I exit with error code if no tests were run:

    >>> ZeroApp.run_in_test_mode(
    ...   args=['build'],
    ...   tests_run=0
    ... ).filter("EXIT")
    EXIT => 1
    """

    def __init__(self, args=None, terminal=None, tests=None):
        self.args = Args() if args is None else args
        self.terminal = Terminal() if terminal is None else terminal
        self.tests = Tests() if tests is None else tests

    def run(self):
        if self.args.get() == ["build"]:
            self.tests.add_doctest("zero")
            self.tests.add_doctest("rlci")
            successful, count = self.tests.run()
            if not successful or count <= 0:
                sys.exit(1)
        else:
            self.terminal.print_line("I am a tool for zero friction development of RLCI.")
            self.terminal.print_line("")
            self.terminal.print_line("Run all tests with")
            self.terminal.print_line("")
            self.terminal.print_line("    ./zero.py build")
            sys.exit(1)

    @staticmethod
    def run_in_test_mode(args=[], tests_succeed=True, tests_run=1):
        events = Events()
        args = Args.create_null(args)
        terminal = Terminal.create_null()
        terminal.register_event_listener(events)
        tests = Tests.create_null(was_successful=tests_succeed, tests_run=tests_run)
        tests.register_event_listener(events)
        app = ZeroApp(args=args, terminal=terminal, tests=tests)
        try:
            app.run()
        except SystemExit as e:
            events.notify("EXIT", e.code)
        return events

class Tests(Observable):

    """
    I am a infrastructure wrapper for Python's test modules.

    I run doctests, print report to stderr, and return success/number of tests
    run:

    >>> result = subprocess.run([
    ...     "python", "-c",
    ...     "import zero;"
    ...     "tests = zero.Tests();"
    ...     "tests.add_doctest('doctest_testmodule');"
    ...     "print(tests.run())",
    ... ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    >>> b'Ran 1 test' in result.stderr
    True
    >>> result.stdout
    b'(True, 1)\\n'

    The null version of me runs no tests for real but instead returns simulated
    responses:

    >>> tests = Tests.create_null(was_successful=False, tests_run=5)
    >>> tests.add_doctest("doctest_testmodule")
    >>> tests.run()
    (False, 5)

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
    def create_null(was_successful=True, tests_run=0):
        class NullUnittest:
            def TestSuite(self):
                return NullTestSuite()
            def TextTestRunner(self):
                return NullTextTestRunner()
        class NullTextTestRunner:
            def run(self, suite):
                return NullResult()
        class NullResult:
            testsRun = tests_run
            def wasSuccessful(self):
                return was_successful
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
