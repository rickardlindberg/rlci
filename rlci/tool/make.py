#!/usr/bin/env python

import os
import subprocess
import sys

RLMETA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "rlmeta", "rlmeta.py"
)

def tool():
    print("Make tool")
    with open("tool.py", "wb") as f:
        f.write(subprocess.run([
            "python", RLMETA_PATH,
            "--copy", "src/header.py",
            "--support",
            "--compile", "src/tool.rlmeta",
            "--copy", "src/footer.py",
        ], check=True, stdout=subprocess.PIPE).stdout)

def test():
    tool()
    print("Make test")
    subprocess.run(["python", "test.py"], check=True)

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    try:
        test()
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
