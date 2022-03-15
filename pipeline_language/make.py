#!/usr/bin/env python

import sys
import os
import subprocess

RLMETA_PATH = os.path.join(os.path.dirname(__file__), "..", "rlmeta", "rlmeta.py")

def pipeline():
    with open("pipeline.py", "wb") as f:
        f.write(subprocess.check_output([
            "python", RLMETA_PATH,
            "--support",
            "--compile", "pipeline.rlmeta",
            "--copy", "pipeline_main.py",
        ]))

def example():
    sys.stdout.buffer.write(subprocess.check_output([
        "python", "pipeline.py",
        "example.pipeline",
    ]))

if __name__ == "__main__":
    pipeline()
    example()
