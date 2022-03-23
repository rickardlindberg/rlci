#!/usr/bin/env python

import sys
import os
import subprocess

RLMETA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "rlmeta", "rlmeta.py")

def tool():
    print("Make tool")
    with open("tool.py", "wb") as f:
        f.write(subprocess.check_output([
            "python", RLMETA_PATH,
            "--support",
            "--compile", "tool.rlmeta",
            "--copy", "footer.py",
        ]))

def example(name):
    tool()
    print(f"Make {name}")
    sys.stdout.buffer.write(subprocess.check_output([
        "python", "tool.py",
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
