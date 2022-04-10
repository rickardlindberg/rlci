#!/usr/bin/env python

import os
import shutil
import subprocess
import sys

TOOL_DIR = os.path.join(os.path.dirname(__file__), "..", "tool")

def tool():
    subprocess.run(
        [sys.executable, os.path.join(TOOL_DIR, "make.py")],
        check=True
    )

def test():
    tool()
    print("Make test")
    subprocess.run(
        [sys.executable, "test/test_server.py"],
        check=True
    )

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    try:
        test()
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
