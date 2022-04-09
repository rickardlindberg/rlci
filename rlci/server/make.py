#!/usr/bin/env python

import os
import subprocess
import sys

def test():
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
