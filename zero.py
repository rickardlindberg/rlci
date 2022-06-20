#!/usr/bin/env python3

import doctest
import importlib
import subprocess
import sys
import unittest

from rlci import Events, Terminal, Observable, Args

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
    DOCTEST_MODULE => 'rlci.pipelines'
    DOCTEST_MODULE => 'rlci.infrastructure'
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

    ## Integrating

    I integrate code by pushing changes to a branch and triggering the
    pre-defined pipeline.

    >>> ZeroApp.run_in_test_mode(args=['integrate'])
    RUN => 'git checkout -b BRANCH'
    RUN => 'git push --set-upstream origin BRANCH'
    RUN => 'python rlci.py trigger'
    RUN => 'git checkout main'
    RUN => 'git pull --ff-only'
    RUN => 'git branch -d BRANCH'
    RUN => 'git push origin BRANCH --delete'
    """

    def __init__(self, args=None, terminal=None, tests=None, shell=None):
        self.args = Args() if args is None else args
        self.terminal = Terminal() if terminal is None else terminal
        self.tests = Tests() if tests is None else tests
        self.shell = Shell() if shell is None else shell

    def run(self):
        if self.args.get() == ["build"]:
            self.tests.add_doctest("zero")
            self.tests.add_doctest("rlci")
            self.tests.add_doctest("rlci.pipelines")
            self.tests.add_doctest("rlci.infrastructure")
            successful, count = self.tests.run()
            if not successful or count <= 0:
                sys.exit(1)
        elif self.args.get() == ["integrate"]:
            self.shell.run("git checkout -b BRANCH")
            self.shell.run("git push --set-upstream origin BRANCH")
            self.shell.run("python rlci.py trigger")
            self.shell.run("git checkout main")
            self.shell.run("git pull --ff-only")
            self.shell.run("git branch -d BRANCH")
            self.shell.run("git push origin BRANCH --delete")
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
        shell = Shell.create_null()
        shell.register_event_listener(events)
        app = ZeroApp(args=args, terminal=terminal, tests=tests, shell=shell)
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
    >>> tests.run()
    (False, 5)

    I log my actions (tested using null version):

    >>> events = Events()
    >>> tests = Tests.create_null()
    >>> tests.register_event_listener(events)
    >>> tests.add_doctest("irrelevant_module_name")
    >>> _ = tests.run()
    >>> events
    DOCTEST_MODULE => 'irrelevant_module_name'
    TEST_RUN => None
    """

    def __init__(self, unittest=unittest, doctest=doctest, importlib=importlib):
        Observable.__init__(self)
        self.unittest = unittest
        self.doctest = doctest
        self.importlib = importlib
        self.suite = unittest.TestSuite()

    def add_doctest(self, module_name):
        self.notify("DOCTEST_MODULE", module_name)
        self.suite.addTest(
            self.doctest.DocTestSuite(
                self.importlib.import_module(module_name)))

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
        class NullImportLib:
            def import_module(self, name):
                pass
        return Tests(
            unittest=NullUnittest(),
            doctest=NullDoctest(),
            importlib=NullImportLib()
        )

class Shell(Observable):

    """
    I can run commands:

    >>> subprocess.run([
    ...     "python", "-c",
    ...     "import zero;"
    ...     "zero.Shell().run('echo hello');"
    ... ], stdout=subprocess.PIPE).stdout
    b'hello\\n'

    The null version of me does not run anything:

    >>> subprocess.run([
    ...     "python", "-c",
    ...     "import zero;"
    ...     "zero.Shell.create_null().run('echo hello');"
    ... ], stdout=subprocess.PIPE).stdout
    b''

    I fail if command fails:

    >>> Shell().run('exit 1')
    Traceback (most recent call last):
        ...
    subprocess.CalledProcessError: Command 'exit 1' returned non-zero exit status 1.

    I log my commands:

    >>> events = Events()
    >>> shell = Shell.create_null()
    >>> shell.register_event_listener(events)
    >>> shell.run("echo hello")
    >>> events
    RUN => 'echo hello'
    """

    def __init__(self, subprocess=subprocess):
        Observable.__init__(self)
        self.subprocess = subprocess

    def run(self, command):
        self.notify("RUN", command)
        self.subprocess.run(command, shell=True, check=True)

    @staticmethod
    def create_null():
        class NullSubprocess:
            def run(self, command, shell, check):
                pass
        return Shell(NullSubprocess())

if __name__ == "__main__":
    ZeroApp().run()
