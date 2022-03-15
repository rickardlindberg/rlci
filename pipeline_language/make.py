#!/usr/bin/env python

import sys
import os
import subprocess

RLMETA_PATH = os.path.join(os.path.dirname(__file__), "..", "rlmeta", "rlmeta.py")

def pipeline():
    print("Make pipeline")
    with open("pipeline.py", "wb") as f:
        f.write(subprocess.check_output([
            "python", RLMETA_PATH,
            "--support",
            "--compile", "pipeline.rlmeta",
            "--copy", "pipeline_main.py",
        ]))

def example():
    pipeline()
    print("Make example")
    sys.stdout.buffer.write(subprocess.check_output([
        "python", "pipeline.py",
        "example.pipeline",
    ]))

def example_dotty():
    example()
    print("Make example dotty")
    subprocess.check_call([
        "dotty",
        "example.dot",
    ])

if __name__ == "__main__":
    example_dotty()
