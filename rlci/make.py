#!/usr/bin/env python

import asyncio
import contextlib
import os
import subprocess
import sys

RUN_TARGETS = {}
def target(dependencies=[], alias=False):
    def inner_target(fn):
        def run_target():
            if RUN_TARGETS[name]["run"]:
                return
            for dependency in dependencies:
                RUN_TARGETS[dependency]["fn"]()
            if not alias:
                print(f"\033[0;35mMaking '{name}'\033[0m")
                fn()
            RUN_TARGETS[name]["run"] = True
        name = fn.__name__.replace('_', '/')
        RUN_TARGETS[name] = {"fn": run_target, "run": False}
        return run_target
    return inner_target

@target()
def tool_build():
    with cd("tool"):
        with open("tool.py", "wb") as f:
            f.write(subprocess.run([
                sys.executable, "../../rlmeta/rlmeta.py",
                "--copy", "src/header.py",
                "--support",
                "--compile", "src/tool.rlmeta",
                "--copy", "src/footer.py",
            ], check=True, stdout=subprocess.PIPE).stdout)

@target(dependencies=["tool/build"])
def tool_test():
    with cd("tool"):
        subprocess.run(
            [sys.executable, "test/test_tool.py"],
            check=True
        )

@target(dependencies=["tool/test"], alias=True)
def tool():
    pass

@target(dependencies=["tool"])
def server_test():
    subprocess.run(
        [sys.executable, "test/test_server.py"],
        check=True,
        cwd="server",
        env={
            "PYTHONPATH": ":".join([
                os.path.join(ROOT, "ipc", "src"),
                os.path.join(ROOT, "tool"),
                os.path.join(ROOT, "server", "src"),
            ])
        }
    )

@target(dependencies=["server/test"], alias=True)
def server():
    pass

@target(dependencies=[], alias=True)
def web():
    pass

@target(dependencies=["server"])
def web_devserver():
    with cd("web"):
        run_processes([
            {
                "name": "web",
                "color": "32",
                "args": [
                    sys.executable, "-m", "flask", "run"
                ],
                "kwargs": {
                    "cwd": "src",
                    "env": {
                        "FLASK_APP": "rlciweb",
                        "FLASK_ENV": "development",
                        "RLCI_SERVER_ADDRESS": "localhost",
                        "RLCI_SERVER_PORT": "9000",
                        "PYTHONPATH": os.path.join(ROOT, "ipc", "src"),
                    }
                },
            },
            {
                "name": "server",
                "color": "33",
                "args": [
                    sys.executable, os.path.join(ROOT, "server", "src", "server.py")
                ],
                "kwargs": {
                    "env": {
                        "PYTHONPATH": os.path.join(ROOT, "ipc", "src"),
                    }
                },
            },
        ])

@target(dependencies=["server", "tool", "web"], alias=True)
def root():
    pass

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
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass

@contextlib.contextmanager
def cd(path):
    cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(cwd)

if __name__ == "__main__":
    try:
        cwd = os.getcwd()
        with cd(os.path.dirname(__file__)):
            ROOT = os.getcwd()
            for arg in sys.argv[1:] or [""]:
                path = os.path.relpath(os.path.join(cwd, arg))
                if path.startswith("."):
                    path = "root"
                RUN_TARGETS[path]["fn"]()
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
