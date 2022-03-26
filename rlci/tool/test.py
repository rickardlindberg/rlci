#!/usr/bin/env python

import json
import os
import subprocess
import tempfile
import unittest

def get_first_stage_definition(pipeline_text):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "test.pipeline")
        with open(path, "w") as f:
            f.write(pipeline_text)
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
                stage {
                    sh "echo foo = ${foo}"
                    sh "echo bar = ${bar}"
                    sh summary "echo ${foo} + ${bar}"
                    out summary "out = ${summary}"
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
                stage {
                    sh "echo ${nonExistingInput}"
                }
            """, []),
            [
                ["Result", "failure", "'nonExistingInput'"],
            ]
        )

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    unittest.main()
