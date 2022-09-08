import os
import socket
import subprocess
import sys

path = sys.argv[1]
try:
    os.remove(path)
except FileNotFoundError:
    pass
s = socket.socket(family=socket.AF_UNIX)
s.bind(path)

os.dup2(s.fileno(), 0)
os.close(s.fileno())

subprocess.call(sys.argv[2:])
