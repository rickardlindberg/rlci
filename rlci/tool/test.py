#!/usr/bin/env python

import contextlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

class EqAny:
    def __eq__(self, other):
        return True

@contextlib.contextmanager
def temporary_pipeline(pipeline):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "test.pipeline")
        with open(path, "w") as f:
            f.write(pipeline)
        yield path

def get_first_stage_definition(pipeline_text):
    with temporary_pipeline(pipeline_text) as path:
        return subprocess.run(
            ["python", "tool.py", "get_stage_definition", path, "0"],
            capture_output=True,
            check=True
        ).stdout

def run_first_stage(pipeline_text, args):
    return [
        json.loads(x)
        for x
        in subprocess.run(
            ["python", "tool.py", "run"]+args,
            capture_output=True,
            check=True,
            input=get_first_stage_definition(pipeline_text)
        ).stdout.splitlines()
    ]

class StageRunner(unittest.TestCase):

    def test_basic_run_happy_path(self):
        self.assertEqual(
            run_first_stage("""
                pipeline {
                    stage {
                        sh "echo foo = ${foo}"
                        sh "echo bar = ${bar}"
                        sh summary "echo ${foo} + ${bar}"
                        out summary "out = ${summary}"
                    }
                }
            """, ["foo=123", "bar=456"]),
            [
                ["Log", "stdout", "foo = 123"],
                ["Log", "stdout", "bar = 456"],
                ["Log", "stdout", "123 + 456"],
                ["Result", "success", {"summary": "out = 123 + 456"}],
            ]
        )

    def test_variable_error(self):
        self.assertEqual(
            run_first_stage("""
                pipeline {
                    stage {
                        sh "echo ${nonExistingInput}"
                    }
                }
            """, []),
            [
                ["Result", "failure", "'nonExistingInput'"],
            ]
        )

class Compile(unittest.TestCase):

    maxDiff = 10000

    def test_minimal(self):
        self.assertCompilesTo("""
            pipeline {
            }
        """, [
            ['Pipeline', {'name': ''}]
        ])

    def test_minimal_with_name(self):
        self.assertCompilesTo("""
            pipeline {
                name "foo"
            }
        """, [
            ['Pipeline', {'name': 'foo'}]
        ])

    def test_stage(self):
        self.assertCompilesTo("""
            pipeline {
                stage {
                    name "foo"
                    sh "echo foo"
                }
            }
        """, [
            ['Pipeline',
              {'name': ''},
              ['Node',
               0,
               {'name': 'foo', 'triggers': []},
               [['StageSh',
                 '',
                 ['String',
                  ['Char', 'e'],
                  ['Char', 'c'],
                  ['Char', 'h'],
                  ['Char', 'o'],
                  ['Char', ' '],
                  ['Char', 'f'],
                  ['Char', 'o'],
                  ['Char', 'o']]]]]]
        ])

    def test_link(self):
        self.assertCompilesTo("""
            pipeline {
                seq {
                    stage { name "foo" }
                    stage { name "bar" }
                }
            }
        """, [
            ['Pipeline',
              {'name': ''},
              ['Node', 0, {'name': 'foo', 'triggers': []}, []],
              ['Node', 1, {'name': 'bar', 'triggers': []}, []],
              ['Link', 0, 1]]
        ])

    def test_triggers(self):
        self.assertCompilesTo("""
            pipeline {
                stage {
                    trigger type="commit" repo="foo"
                }
            }
        """, [
            ['Pipeline',
              {'name': ''},
              ['Node',
               0,
               {'name': '0', 'triggers': [{'repo': 'foo', 'type': 'commit'}]},
               []]]
        ])

    def test_example(self):
        with open("example.pipeline") as f:
            self.assertCompilesTo(f.read(), EqAny())

    def assertCompilesTo(self, pipeline, output):
        with temporary_pipeline(pipeline) as path:
            result = subprocess.run(
                ["python", "tool.py", "compile", path],
                capture_output=True
            )
            try:
                if result.returncode != 0:
                    self.fail(f"Compilation of {path} failed")
                self.assertEqual(json.loads(result.stdout), output)
            except:
                sys.stderr.buffer.write(result.stderr)
                raise

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    unittest.main(verbosity=2)
