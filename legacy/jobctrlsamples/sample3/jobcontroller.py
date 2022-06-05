"""
A prototype for a running a workflow of tasks.

Task: Definition of work to be done
  A task has a list of other tasks that it is waiting for to be finished.
  When all the tasks in this list has finished the task is executed.
  A task reports back to the JobController, with a callback function when
  it has finished.

JobController: Running Tasks in a predefined order.
  The controller has two lists:
    * Tasks waiting to be started
    * Finished tasks

  The controller places all tasks in the waiting-list and starts them all.
  The task itself checks if it ok to run or wait for other tasks to complete.

  When a task finishes it uses the callback function in the JobController to report this.
  When this happens the task is moved from the waiting-list to the finished-list.

  Graphwiz is used to produce a svg image of the task flow. This image is updated
  when a task starts to fill the task node with a blue color. An ended task is
  colored green, red or yellow depending on task result (ok, skipped, failed).
  A hyperlink is created in the node for a fished task that is used to display
  a detailed task result.

  As a proof of concept, the Timeline build chain for producing a windows installer is
  implemented.
"""

from __future__ import annotations

from typing import List, Union
import sys
import os
import subprocess
import asyncio
import random
from workflowdrawer import WorkflowDrawer
import time
import datetime


OK = 0
FAILED = 1
SKIPPED = 2
STOPPED = 3
STATUS_DESCRIPTIONS = {
    0: "OK",
    1: "Failed",
    2: "Skipped",
    3: "Stopped",
}
GREEN = '"#B2FEB2"'
YELLOW = '"#FDFEB2"'
RED = '"#F63E3E"'
BLUE = '"#C0FFFF"'
LILAC = '"#FFC0FF"'


class Task:
    def __init__(self, name, description):
        self._name = name
        self._fillcolor = "white"
        self._description = description
        self._wait_for = []
        self._original_waits = []
        self._started_at = None
        self._ended_at = None
        self._start_dt = None
        self._end_dt = None
        self._status = OK
        self._run_on_fail = []
        self._run_on_skip = []
        self._stdout = ""
        self._stderr = ""
        self._url = ""
        self._cwd = "."
        self._return_code = 0
        self._input = ""
        self._except = ""
        self._command = ""
        self._result = ""

    @property
    def name(self) -> str:
        """The name (identity) of the task."""
        return self._name

    @property
    def description(self) -> str:
        """A verbal description of the task."""
        return self._description

    @property
    def fillcolor(self) -> str:
        """The color to use when rendering the task in a graph."""
        return self._fillcolor

    @property
    def stdout(self) -> str:
        """The standard output from a task work."""
        return self._stdout

    @property
    def stderr(self) -> str:
        """The standard error from a task work."""
        return self._stderr

    @property
    def url(self) -> str:
        """The url to be used for hyperlinks in a rendered graph."""
        return self._url

    @property
    def wait(self) -> List[str]:
        """The list of other tasks (names) to wait for."""
        return self._wait_for

    @property
    def original_waits(self) -> List[str]:
        """The list of other tasks (names) to wait for as it looked when the job was started."""
        return self._wait_for

    @wait.setter
    def wait(self, value: List[str]) -> None:
        """Specify which tasks to wait for."""
        self._wait_for = value
        self._original_waits = value

    def __repr__(self) -> str:
        """A string representation of a task."""
        return f"<Task {self._name} at {hex(id(self))}>"

    @property
    def ok(self) -> bool:
        """Return True if task status is OK."""
        return self._status == OK

    @property
    def failed(self) -> bool:
        """Return True if task status is FAILED."""
        return self._status == FAILED

    @property
    def skipped(self) -> bool:
        """Return True if task status is SKIPPED."""
        return self._status == SKIPPED

    @property
    def stopped(self) -> bool:
        """Return True if task status is STOPPED."""
        return self._status == STOPPED

    @property
    def status(self) -> str:
        """Return the current status for the task."""
        return STATUS_DESCRIPTIONS[self._status]

    @property
    def run_on_fail(self) -> List[str]:
        """Return a list of tasks (names) that are ignored if they fail."""
        return self._run_on_fail

    @property
    def run_on_skip(self) -> List[str]:
        """Return a list of tasks (names) that are ignored if they are skipped."""
        return self._run_on_skip

    #
    # Commands
    #

    def run_when_fails(self, names: list[str]) -> Task:
        """Specify a list of tasks (names) that are ignored if they fail."""
        self._run_on_fail = names
        return self

    def run_when_skips(self, names: list[str]) -> Task:
        """Specify a list of tasks (names) that are ignored if they are skipped."""
        self._run_on_skip = names
        return self

    def debug(self) -> Task:
        """Run task in debug mode."""
        self._debug = True
        return self

    def stop(self) -> Task:
        """Stop this task from executing"""
        self._status = STOPPED
        return self

    def wait_for(self, task_name: List[str]) -> Task:
        """Specify a list of tasks (names) to wait for."""
        self._wait_for.append(task_name)
        return self

    def cwd(self, cwd: str) -> Task:
        """Specify teh Current Working Directory fo rthe task execution."""
        self._cwd = cwd
        return self

    def input(self, input: Union[str, List[str]]) -> Task:
        self._input = input
        return self

    def skip(self) -> Task:
        """Skip this task from execution."""
        self._status = SKIPPED
        self._fillcolor = YELLOW
        self._started_at = time.time()
        self._start_dt = f"{datetime.datetime.now()}"
        self._ended_at = self._started_at
        self._end_dt = f"{datetime.datetime.now()}"
        return self

    async def run(self, callback, drawer):
        if self.skipped:
            print(f"[JOBCTRL] Task skipped : {self}")
            self._fillcolor = YELLOW
            self._ended_at = time.time()
            self._end_dt = f"{datetime.datetime.now()}"
            drawer.draw()
            callback(self)
        else:
            while self._wait_for:
                await asyncio.sleep(0.1)
            self._started_at = time.time()
            self._start_dt = f"{datetime.datetime.now()}"
            if self.stopped:
                self._fillcolor = LILAC
                self._ended_at = time.time()
                self._end_dt = f"{datetime.datetime.now()}"
                drawer.draw()
                callback(self)
            elif self.skipped:
                print(f"[JOBCTRL] Task skipped : {self}")
                self._fillcolor = YELLOW
                self._ended_at = time.time()
                self._end_dt = f"{datetime.datetime.now()}"
                drawer.draw()
                callback(self)
            else:
                print(f"[JOBCTRL] Task started : {self}")
                self._fillcolor = BLUE
                drawer.draw()
                try:
                    self._return_code = await self._do_work()
                    # if self.name.startswith("T11"):
                    #     self._status = SKIPPED
                    # elif self.name.startswith("T12"):
                    #     self._status = FAILED
                except Exception as ex:
                    self._status = FAILED
                    self._except = str(ex)
                    self._return_code = 9
                finally:
                    self._ended_at = time.time()
                    self._end_dt = f"{datetime.datetime.now()}"
                    if self.ok:
                        self._fillcolor = GREEN
                    elif self.skipped:
                        self._fillcolor = YELLOW
                    elif self.failed:
                        self._fillcolor = RED
                    drawer.draw()
                    callback(self)
        try:
            self._create_result_html_page()
        except Exception as ex:
            print("EX:", ex)
            pass

    async def _do_work(self):
        """Default action"""
        os.chdir(self._cwd)
        self._command = "asyncio.sleep(random.randint(5, 15))"
        await asyncio.sleep(random.randint(5, 15))
        self._result = "Woke up from sleep"
        return 0

    def report(self):
        collector = []
        collector.append(f"{'=' * 70}")
        collector.append(f"Report from task: {self._name}:")
        collector.append(f"  Description: {self._description}")
        collector.append(f"  Input      : {self._input}")
        collector.append(f"  Command    : {self._command}")
        collector.append(f"  Status     : {self.status}")
        collector.append(f"  Return Code: {self._return_code}")
        collector.append(f"  Result     : {self._result}")
        collector.append(f"  Started at : {self._start_dt}")
        collector.append(f"  Run-time   : {(self._ended_at - self._started_at):.1f}")
        collector.append(f"  Ended at   : {self._end_dt}")
        collector.append(f"  Cwd        : {self._cwd}")
        collector.append(f"  Exception  : {self._except}")
        if self._stdout and len(self._stdout.strip()) > 0:
            collector.append("----(STDOUT)-----")
            collector.append(self._stdout)
        if self._stderr and len(self._stderr.strip()) > 0:
            collector.append("----(STDERR)-----")
            collector.append(self._stderr)
        return "\n".join(collector)

    def _create_result_html_page(self):
        TEMPLATE = f"""
        <!DOCTYPE html>
        <html>
          <head>
          </head>
          <body>
            <pre>
{self.report()}
            </pre>
          </body>
        </html>
        """
        self._url = f"{self._name}.html"
        with open(self._url, "w") as f:
            f.write(TEMPLATE)


class SubprocessTask(Task):
    """Run a subprocess task."""

    async def _do_work(self):
        os.chdir(self._cwd)
        self._command = " ".join(self._input)
        returncode = await self._process()
        if returncode == 0:
            self._result = "subprocess completed successfully"
        else:
            self._result = "subprocess had problems."
            raise Exception(f"Rc == {returncode}")
        return returncode

    async def _process(self):
        process = await asyncio.create_subprocess_exec(
            *self._input, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        self._stdout = stdout.decode()
        self._stderr = stderr.decode()
        return process.returncode


class ShellTask(Task):
    """Run a shell task."""

    async def _do_work(self):
        self._command = self._input
        os.chdir(self._cwd)
        returncode = await self._process()
        if returncode == 0:
            self._result = "subprocess completed successfully"
        else:
            self._result = "subprocess had problems."
            raise Exception(f"Rc == {returncode}")
        return returncode

    async def _process(self):
        process = await asyncio.create_subprocess_shell(
            self._input, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        self._stdout = stdout.decode()
        self._stderr = stderr.decode()
        return process.returncode


class JobController:
    """
    Kepp track of tasks to be run.
    """

    def __init__(self):
        self._waiting_tasks = []
        self._finished_tasks = []
        self._running_tasks = []
        self._start_tasks = []

    def add_tasks(self, tasks):
        self._waiting_tasks.extend(tasks)

    async def start(self):
        self._remove_old_html_files()
        self._workflow_drawer = WorkflowDrawer(self._waiting_tasks)
        self._workflow_drawer.draw()
        print("[JOBCTRL] Job started  :")
        await asyncio.gather(
            *[
                t.run(self.task_finished, self._workflow_drawer)
                for t in self._waiting_tasks
            ]
        )
        self._workflow_drawer.draw(done=True)
        print("[JOBCTRL] Job finsished:")

    def _remove_old_html_files(self):
        for file in os.listdir("."):
            if file.endswith(".html") and file != "sample1.html":
                os.unlink(os.path.join(".", file))

    def _can_start(self, task):
        task.wait = list(
            set(task.wait).difference(set([task.name for task in self._finished_tasks]))
        )
        return len(task.wait) == 0

    def task_finished(self, task):
        if task.stopped:
            print(f"[JOBCTRL] Task stopped : {task}")
        else:
            self._finished_tasks.append(task)
            print(f"[JOBCTRL] Task finished: {task}")
            for t in [t for t in self._waiting_tasks if t != task]:
                if task.name in t._wait_for:
                    if task.failed and task.name not in t.run_on_fail:
                        t._wait_for.clear()
                        t.skip()
            for t in [t for t in self._waiting_tasks if t != task]:
                if task.name in t._wait_for:
                    if task.skipped and task.name not in t.run_on_skip:
                        t._wait_for.clear()
                        t.skip()
            for t in [t for t in self._waiting_tasks if t != task]:
                if task.name in t._wait_for:
                    t._wait_for.remove(task.name)
        self._workflow_drawer.draw()


async def test():
    """
                      +--> T2 -->|
                      |          |
    Start------------>+--> T3--->|--> T6  -->|
                      |          |           |--> T8  -->|--> T10 --------------------->|--> T17 -->|
                      +--> T4 -->|           |--> T9  -->|                              |
                                             |--> T11 -->|---------->|--> T13 -->|      |
                                             |--> T12 -->|           |--> T14 -->|----->|
                                                                     |--> T15 -->|      |
    """
    TOOLS_DIR = os.path.join(
        "C:\\Projects", "OpenSourceProjects", "Timeline", "main", "tools"
    )
    WINTOOLS_DIR = os.path.join(
        "C:\\Projects",
        "OpenSourceProjects",
        "Timeline",
        "main",
        "tools",
        "winbuildtools",
    )
    INNO_DIR = os.path.join(
        "C:\\Projects",
        "OpenSourceProjects",
        "Timeline",
        "main",
        "tools",
        "winbuildtools",
        "inno",
    )

    jc = JobController()
    jc.add_tasks(
        [
            ShellTask("T1A", "Delete old build dir")
                .cwd(TOOLS_DIR)
                .input(
                    f'IF exist {os.path.join(TOOLS_DIR, "winbuildtools", "build")} ( del /S /Q {os.path.join(TOOLS_DIR, "winbuildtools", "build")} )'
            ),
            ShellTask("T1B", "Delete old dist dir")
                .input(
                f'IF exist {os.path.join(TOOLS_DIR, "winbuildtools", "dist")} ( del /S /Q {os.path.join(TOOLS_DIR, "winbuildtools", "dist")} )'
            ),
            ShellTask("T2", "Remove old build dir")
                .cwd(TOOLS_DIR)
                .input(f'IF exist {os.path.join(TOOLS_DIR, "winbuildtools", "build")} ( rmdir /S /Q {os.path.join(TOOLS_DIR, "winbuildtools", "build")} )')
                .wait_for("T1A"),
            ShellTask("T3", "Remove old dist dir")
                .cwd(TOOLS_DIR)
                .input(f'IF exist {os.path.join(TOOLS_DIR, "winbuildtools", "build")} ( rmdir /S /Q {os.path.join(TOOLS_DIR, "winbuildtools", "dist")} )')
                .wait_for("T1B"),
            ShellTask("T4", "Remove content of output dir")
                .cwd(TOOLS_DIR)
                .input(f'del /S /Q {os.path.join(TOOLS_DIR, "winbuildtools", "inno", "out")}'),
            SubprocessTask("T6", "Generate mo files")
                .cwd(TOOLS_DIR)
                .input(["python", "-m" "generate-mo-files"]),
            SubprocessTask("T8", "Modify paths.py")
                .cwd(WINTOOLS_DIR)
                .input(["python", "-m", "mod_paths", "."]),
            SubprocessTask("T9", "Modify version file and iss file")
                .cwd(WINTOOLS_DIR)
                .input(["python", "-m", "mod_iss_timeline_version", ".", "2.6.0"]),
            ShellTask("T11", "Create icons dir")
                .cwd(WINTOOLS_DIR)
                .input(f'IF not exist {os.path.join(WINTOOLS_DIR, "dist", "icons", "event_icons")} (mkdir {os.path.join(WINTOOLS_DIR, "dist", "icons", "event_icons")})')
                .wait_for("T3"),
            ShellTask("T12", "Create translations dir")
                .cwd(WINTOOLS_DIR)
                .input(f'IF not exist {os.path.join(".", "dist", "translations")} (mkdir {os.path.join(".", "dist", "translations")})')
                .wait_for("T3")
                .wait_for("T6"),
            SubprocessTask("T10", "Building distribution")
                .cwd(WINTOOLS_DIR)
                .input(["pyinstaller", "timeline.spec"])
                .wait_for("T8")
                .wait_for("T9"),
            ShellTask("T13", "Copying icons")
                .cwd(WINTOOLS_DIR)
                .input("xcopy  /S ..\\..\\icons\\*.*  .\\dist\\icons\\*.*")
                .wait_for("T11"),
            ShellTask("T14", "Copying translations")
                .cwd(WINTOOLS_DIR)
                .input(f"xcopy /S ..{os.sep}..{os.sep}translations{os.sep}*.*  .{os.sep}dist{os.sep}translations{os.sep}*.*")
                .wait_for("T12"),
            SubprocessTask("T17", "Build with inno")
                .cwd(INNO_DIR)
                .input(["iscc.exe", "timeline2Win32.iss"])
                .wait_for("T2")
                .wait_for("T4")
                .wait_for("T10")
                .wait_for("T13")
                .wait_for("T14"),
        ]
    )
    await jc.start()


if __name__ == "__main__":
    asyncio.run(test())
