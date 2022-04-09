#!/usr/bin/env python

import os
import shutil
import subprocess
import sys

TOOL_DIR = os.path.join(os.path.dirname(__file__), "..", "tool")

def tool():
    subprocess.check_call([
        "python", os.path.join(TOOL_DIR, "make.py"),
    ])
    shutil.copy(os.path.join(TOOL_DIR, "tool.py"), "tool.py")

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
