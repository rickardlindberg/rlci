#!/usr/bin/env python

import contextlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

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

    def test_triggers(self):
        with temporary_pipeline("""
            pipeline {
                stage {
                    trigger type="commit" repo="foo"
                }
            }
        """) as path:
            self.assertEqual(
                self.compile(path)[0][2][2]["triggers"],
                [
                    {
                        "type": "commit",
                        "repo": "foo",
                    }
                ]
            )

    def test_example_compiles(self):
        self.compile("example.pipeline")

    def compile(self, path):
        result = subprocess.run(
            ["python", "tool.py", "compile", path],
            capture_output=True
        )
        if result.returncode != 0:
            sys.stderr.buffer.write(result.stderr)
            self.fail(f"Compilation of {path} failed")
        return json.loads(result.stdout)

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    unittest.main()
