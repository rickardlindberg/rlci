#!/usr/bin/env python

import sys
import subprocess

def pipeline():
    with open("pipeline.py", "wb") as f:
        f.write(subprocess.check_output([
            "python", "rlmeta/rlmeta.py",
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
