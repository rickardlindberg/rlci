#!/usr/bin/env python3

import doctest
import importlib
import subprocess
import sys
import unittest

from rlci import Events, Observable
from rlci.infrastructure import Args, Terminal, Process

class ZeroApp:

    """
    I am a tool for zero friction development.

    Usage
    =====

    I print usage when run with no arguments:

    >>> ZeroApp.run_in_test_mode(args=[])
    STDOUT => 'I am a tool for zero friction development of RLCI.'
    STDOUT => ''
    STDOUT => 'Run all tests with'
    STDOUT => ''
    STDOUT => '    ./zero.py build'
    EXIT => 1

    Building
    ========

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

    Integrating
    ===========

    I integrate code by pushing changes to a branch and triggering the
    pre-defined pipeline.

    >>> ZeroApp.run_in_test_mode(args=['integrate']).filter("PROCESS", "EXIT")
    PROCESS => ['git', 'checkout', '-b', 'BRANCH']
    PROCESS => ['git', 'push', '--set-upstream', 'origin', 'BRANCH']
    PROCESS => ['ssh', '-t', 'rlci@ci.rickardlindberg.me', 'python', '/opt/rlci/rlci.py', 'trigger', 'rlci']
    PROCESS => ['git', 'checkout', 'main']
    PROCESS => ['git', 'pull', '--ff-only']
    PROCESS => ['git', 'branch', '-d', 'BRANCH']
    PROCESS => ['git', 'push', 'origin', 'BRANCH', '--delete']

    When integration fails, I still delete the temporary branch:

    >>> ZeroApp.run_in_test_mode(args=['integrate'], process_responses=[
    ...     {
    ...         "command": ['ssh', '-t', 'rlci@ci.rickardlindberg.me', 'python',
    ...                     '/opt/rlci/rlci.py', 'trigger', 'rlci'],
    ...         "returncode": 99,
    ...     }
    ... ]).filter("PROCESS", "EXIT")
    PROCESS => ['git', 'checkout', '-b', 'BRANCH']
    PROCESS => ['git', 'push', '--set-upstream', 'origin', 'BRANCH']
    PROCESS => ['ssh', '-t', 'rlci@ci.rickardlindberg.me', 'python', '/opt/rlci/rlci.py', 'trigger', 'rlci']
    PROCESS => ['git', 'checkout', 'main']
    PROCESS => ['git', 'pull', '--ff-only']
    PROCESS => ['git', 'branch', '-d', 'BRANCH']
    PROCESS => ['git', 'push', 'origin', 'BRANCH', '--delete']
    EXIT => 1

    Deploying
    =========

    I deploy a version of RLCI to /opt/rlci:

    >>> ZeroApp.run_in_test_mode(args=['deploy', '<git-hash>']).filter("PROCESS")
    PROCESS => ['find', '/opt/rlci', '-mindepth', '1', '-maxdepth', '1', '-exec', 'rm', '-rf', '{}', ';']
    PROCESS => ['git', 'clone', 'git@github.com:rickardlindberg/rlci.git', '/opt/rlci/']
    PROCESS => ['git', '-C', '/opt/rlci', 'checkout', '<git-hash>']
    PROCESS => ['sudo', 'supervisorctl', 'restart', 'rlci-engine']

    I fail if no version is given:

    >>> ZeroApp.run_in_test_mode(args=['deploy'])
    STDOUT => 'No version given to deploy.'
    EXIT => 1
    """

    def __init__(self, args, terminal, tests, process):
        self.args = args
        self.terminal = terminal
        self.tests = tests
        self.process = ExitLoggingProcess(process, terminal)

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
            self.process.run(["git", "checkout", "-b", "BRANCH"])
            self.process.run(["git", "push", "--set-upstream", "origin", "BRANCH"])
            try:
                self.process.run(["ssh", "-t", "rlci@ci.rickardlindberg.me", "python", "/opt/rlci/rlci.py", "trigger", "rlci"])
            finally:
                self.process.run(["git", "checkout", "main"])
                self.process.run(["git", "pull", "--ff-only"])
                self.process.run(["git", "branch", "-d", "BRANCH"])
                self.process.run(["git", "push", "origin", "BRANCH", "--delete"])
        elif self.args.get()[:1] == ["deploy"]:
            if len(self.args.get()) < 2:
                self.terminal.print_line("No version given to deploy.")
                sys.exit(1)
            version = self.args.get()[1]
            self.process.run(["find", "/opt/rlci", "-mindepth", "1", "-maxdepth", "1", "-exec", "rm", "-rf", "{}", ";"])
            self.process.run(["git", "clone", "git@github.com:rickardlindberg/rlci.git", "/opt/rlci/"])
            self.process.run(["git", "-C", "/opt/rlci", "checkout", version])
            self.process.run(['sudo', 'supervisorctl', 'restart', 'rlci-engine'])
        else:
            self.terminal.print_line("I am a tool for zero friction development of RLCI.")
            self.terminal.print_line("")
            self.terminal.print_line("Run all tests with")
            self.terminal.print_line("")
            self.terminal.print_line("    ./zero.py build")
            sys.exit(1)

    @staticmethod
    def create():
        return ZeroApp(
            args=Args.create(),
            terminal=Terminal.create(),
            tests=Tests.create(),
            process=Process.create()
        )

    @staticmethod
    def run_in_test_mode(args=[], tests_succeed=True, tests_run=1, process_responses=[]):
        events = Events()
        args = Args.create_null(args)
        terminal = Terminal.create_null()
        terminal.register_event_listener(events)
        tests = Tests.create_null(was_successful=tests_succeed, tests_run=tests_run)
        tests.register_event_listener(events)
        process = Process.create_null(responses=process_responses)
        process.register_event_listener(events)
        app = ZeroApp(args=args, terminal=terminal, tests=tests, process=process)
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
    ...     "tests = zero.Tests.create();"
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

    def __init__(self, unittest, doctest, importlib):
        Observable.__init__(self)
        self.unittest = unittest
        self.doctest = doctest
        self.importlib = importlib
        self.suite = unittest.TestSuite()

    def add_doctest(self, module_name):
        self.notify("DOCTEST_MODULE", module_name)
        self.suite.addTest(
            self.doctest.DocTestSuite(
                self.importlib.import_module(module_name),
                optionflags=doctest.REPORT_NDIFF|doctest.FAIL_FAST
            )
        )

    def run(self):
        self.notify("TEST_RUN", None)
        result = self.unittest.TextTestRunner().run(self.suite)
        return (result.wasSuccessful(), result.testsRun)

    @staticmethod
    def create():
        return Tests(
            unittest=unittest,
            doctest=doctest,
            importlib=importlib
        )

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
            def DocTestSuite(self, module, optionflags):
                pass
        class NullImportLib:
            def import_module(self, name):
                pass
        return Tests(
            unittest=NullUnittest(),
            doctest=NullDoctest(),
            importlib=NullImportLib()
        )

class ExitLoggingProcess:

    """
    I run and log commands:

    >>> ExitLoggingProcess.run_in_test_mode(["ls", "/tmp"], responses=[
    ...     {"command": ['ls', '/tmp'], "output": ["foo", "bar"]}
    ... ])
    STDOUT => "['ls', '/tmp']"
    PROCESS => ['ls', '/tmp']
    STDOUT => 'foo'
    STDOUT => 'bar'

    I exit with 1 if a command fails:

    >>> ExitLoggingProcess.run_in_test_mode(["ls", "/tmp"], responses=[
    ...     {"command": ['ls', '/tmp'], "returncode": 99}
    ... ])
    STDOUT => "['ls', '/tmp']"
    PROCESS => ['ls', '/tmp']
    EXIT => 1
    """

    def __init__(self, process, terminal):
        self.process = process
        self.terminal = terminal

    def run(self, command):
        self.terminal.print_line(str(command))
        if self.process.run(command, output=self.terminal.print_line) != 0:
            sys.exit(1)

    @staticmethod
    def run_in_test_mode(command, responses):
        events = Events()
        process = events.listen(Process.create_null(responses=responses))
        terminal = events.listen(Terminal.create_null())
        try:
            ExitLoggingProcess(process, terminal).run(command)
        except SystemExit as e:
            events.notify("EXIT", e.code)
        return events

if __name__ == "__main__":
    ZeroApp.create().run()
