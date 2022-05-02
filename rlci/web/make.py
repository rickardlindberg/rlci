#!/usr/bin/env python

import asyncio
import os
import subprocess
import sys

SRC_DIR = os.path.join(os.path.dirname(__file__), "src")
SERVER_DIR = os.path.join(os.path.dirname(__file__), "..", "server")

def server():
    subprocess.run([
        sys.executable, os.path.join(SERVER_DIR, "make.py"),
    ], check=True)

def devserver():
    server()
    run_processes([
        {
            "name": "web",
            "color": "32",
            "args": [
                sys.executable, "-m", "flask", "run"
            ],
            "kwargs": {
                "cwd": SRC_DIR,
                "env": {
                    "FLASK_APP": "rlciweb",
                    "FLASK_ENV": "development",
                    "RLCI_SERVER_ADDRESS": "localhost",
                    "RLCI_SERVER_PORT": "9000",
                }
            },
        },
        {
            "name": "server",
            "color": "33",
            "args": [
                sys.executable, os.path.join(SERVER_DIR, "src", "server.py")
            ],
            "kwargs": {
            },
        },
    ])

def run_processes(process_descriptions):
    async def read_stdout(name, color, process):
        keep_going = True
        while keep_going:
            line = await process.stdout.readline()
            if not line:
                keep_going = False
                line = b"PROCESS EXITED"
            sys.stdout.buffer.write(f"\033[0;{color}m".encode("utf-8"))
            sys.stdout.buffer.write(name.encode("utf-8").ljust(8))
            sys.stdout.buffer.write(line.rstrip(b"\n"))
            sys.stdout.buffer.write(b"\n")
            sys.stdout.buffer.write(b"\033[0m")
            sys.stdout.flush()
    async def run():
        tasks = []
        for description in process_descriptions:
            process = await asyncio.create_subprocess_exec(
                *description["args"],
                **description["kwargs"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            tasks.append(read_stdout(description["name"], description["color"], process))
        await asyncio.gather(*tasks)
    asyncio.run(run())

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    try:
        devserver()
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
