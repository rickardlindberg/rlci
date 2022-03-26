#!/usr/bin/env python

import os
import subprocess
import sys

RLMETA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "rlmeta")
RLMETA_PATH = os.path.join(RLMETA_DIR, "rlmeta.py")

def rlmeta():
    subprocess.check_call([
        "python", os.path.join(RLMETA_DIR, "make.py"),
    ])

def tool():
    rlmeta()
    print("Make tool")
    with open("tool.py", "wb") as f:
        f.write(subprocess.check_output([
            "python", RLMETA_PATH,
            "--copy", "src/header.py",
            "--support",
            "--compile", "src/tool.rlmeta",
            "--copy", "src/footer.py",
        ]))

def test():
    tool()
    print("Make test")
    subprocess.check_output([
        "python", "test.py",
    ])

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    try:
        test()
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
