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

def example(name):
    pipeline()
    print(f"Make {name}")
    sys.stdout.buffer.write(subprocess.check_output([
        "python", "pipeline.py",
        f"{name}.pipeline",
    ]))

def dotty(name):
    example(name)
    print("Make example dotty")
    subprocess.check_call([
        "dotty",
        f"{name}.dot",
    ])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        name = sys.argv[1]
    else:
        name = "example"
    dotty(name)
