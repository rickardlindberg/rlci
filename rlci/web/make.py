#!/usr/bin/env python

import os
import subprocess
import sys

SRC_DIR = os.path.join(os.path.dirname(__file__), "src")
TOOL_DIR = os.path.join(os.path.dirname(__file__), "..", "tool")

def tool():
    subprocess.check_call([
        "python", os.path.join(TOOL_DIR, "make.py"),
    ])

def devserver():
    tool()
    subprocess.check_call([
        "python", "-m", "flask", "run"
    ], cwd=SRC_DIR, env={"FLASK_APP": "rlciweb"})

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    try:
        devserver()
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
