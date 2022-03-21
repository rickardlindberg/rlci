"""
A prototype for a running a workflow of tasks.

Task: Definition ow work to be done
  A task has a list of other tasks that it is waiting for to be finished.
  When all the tasks in this list has finished the task is executed.
  A task reports back to the JobController, with a callback function when
  it has finished.

JobController: Running Tasks in a predefined order.
  The controller has for lists:
    * Tasks waiting to be started
    * Tasks to start
    * Running tasks
    * Finished tasks
  The controller has a loop that continues as long as the first three lists has any items.
  Tasks in the waiting list are moved to the "Tasks to start list" when all the tasks it is
  waiting for has finsihed.
  An asyncio-loop starts the tasks in the "Tasks to start list" and they are then moved to
  to the "Running tasks" list.
  When a task finishes it uses the callback function in the JobController to report this.
  When this happens the task is moved from the "Running tasks" list to the "Finished tasks"
  list.

Future ideas:
  More sofisticated ways to decide if a task should start (at a certain time etc).
  Ways to skip/fail a task depending on predecessors result.
  Handle failure/exceptions.
  Create nice reports and logs from tasks and controller.
"""

import os
import asyncio
import random
import datetime
import time
import pandas
import networkx
from pyvis.network import Network
import matplotlib.pyplot as plt

OK = 0
FAILED = 1
SKIPPED = 2


class Task:
    def __init__(self, name):
        self._work_to_be_done = None
        self._result = None
        self._started_at = None
        self._ended_at = None
        self._status = 0
        self._name = name
        self._wait_for = []
        self._dependants = []
        self._run_on_skip = []
        self._run_on_fail = []

    def __repr__(self):
        return f"<Task {self._name} at {hex(id(self))}>"

    def command(self, work):
        self._work_to_be_done = work
        return self

    @property
    def dependants(self):
        return self._dependants

    @property
    def ok(self):
        return self._status == OK

    @property
    def failed(self):
        return self._status == FAILED

    @property
    def skipped(self):
        return self._status == SKIPPED

    @property
    def status(self):
        return {
            0: "OK",
            1: "Failed",
            2: "Skipped",
        }[self._status]

    @property
    def name(self):
        return self._name

    @property
    def wait(self):
        return self._wait_for

    @wait.setter
    def wait(self, value):
        self._wait_for = value

    @property
    def result(self):
        return self._result

    @property
    def fails(self):
        return self._run_on_fail

    @property
    def skips(self):
        return self._run_on_skip

    def ignore_fail_for(self, names: list[str]):
        self._run_on_fail = names
        return self

    def ignore_skip_for(self, names: list[str]):
        self._run_on_skip = names
        return self

    def report(self):
        collector = []
        collector.append(f"Report from {self}:")
        collector.append(f"  Status  : {self.status}")
        collector.append(f"  Run-time: {(self._ended_at - self._started_at):.1f}")
        collector.append(f"  Command : {self._work_to_be_done}")
        collector.append(f"  Result:")
        collector.append(str(self._result))
        collector.append(f" ")
        return "\n".join(collector)

    def do_skip(self):
        self._status = SKIPPED
        self._started_at = time.time()
        self._ended_at = self._started_at

    def wait_for(self, task_name):
        self._wait_for.append(task_name)
        self._dependants.append(task_name)
        return self

    async def run(self, callback):
        try:
            self._started_at = time.time()
            # Simulate a failed task
            time_to_sleep = random.randint(1, 10)
            await asyncio.sleep(time_to_sleep)
            if self._work_to_be_done:
                self._result = eval(self._work_to_be_done)
            self._ended_at = time.time()
        except Exception as ex:
            self._status = FAILED
            self._result = str(ex)
        finally:
            callback(self)


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

    def start(self):
        print(self.format_log("Job started  :"))
        while (
            len(self._waiting_tasks) + len(self._running_tasks) + len(self._start_tasks)
            > 0
        ):
            self._process_tasks()
        print(self.format_log("Job finished :"))
        # self.report()

    def report(self):
        for task in self._finished_tasks:
            try:
                print(task.report())
            except:
                print(f"Report for task {task} failed")

    def _process_tasks(self):
        self._move_tasks_from_wait_queue()
        self._do_start_tasks()

    def _move_tasks_from_wait_queue(self):
        for task in self._waiting_tasks:
            if self._can_start(task):
                self._start_tasks.append(task)
        self._waiting_tasks = [
            task for task in self._waiting_tasks if task not in self._start_tasks
        ]
        self._waiting_tasks = [
            task for task in self._waiting_tasks if task not in self._finished_tasks
        ]

    def _can_start(self, task: Task) -> bool:
        """
        First all Task's we are waiting for must be finished.

        If any of the finished Task's is skipped the default behaviour is to skip the task.
        To change this behaviour you can define the tasks that wont be counted when investigating
        finished, skipped tasks, by using the ignore_skip_for([names]) method.

        If any of the finished Task's is failed the default behaviour is to skip the task.
        To change this behaviour you can define the tasks that wont be counted when investigating
        finished, failed tasks, by using the ignore_fail_for([names]) method.

        """
        if self._predecessors_not_finished(task):
            return False
        if self._predecessors_has_failed_or_skipped(task):
            task.do_skip()
            self.task_finished(task)
            return False
        return True

    def _predecessors_has_failed_or_skipped(self, task):
        skipped = [
            t.name
            for t in self._finished_tasks
            if t.name in task.dependants and t.skipped and t.name not in task.skips
        ]
        failed = [
            t.name
            for t in self._finished_tasks
            if t.name in task.dependants and t.failed and t.name not in task.fails
        ]
        return len(skipped) + len(failed) > 0

    def _predecessors_not_finished(self, task):
        finished = [t.name for t in self._finished_tasks]
        for w in task.wait:
            if w not in finished:
                return True
        return False

    def _do_start_tasks(self):
        collector = []
        for task in self._start_tasks:
            collector.append(task)
        self._start_tasks = []
        if len(collector) > 0:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            tasks = [
                new_loop.create_task(self._execute_task(task)) for task in collector
            ]
            new_loop.run_until_complete(asyncio.wait(tasks))
            new_loop.close()

    async def _execute_task(self, task):
        print(self.format_log(f"Task started : {task}"))
        self._running_tasks.append(task)
        await task.run(self.task_finished)

    def task_finished(self, task):
        self._finished_tasks.append(task)
        if task in self._running_tasks:
            self._running_tasks.remove(task)
        print(self.format_log(f"Task finished: {task} Status: {task.status}"))

    def format_log(self, text):
        return f"[JOBCTRL] {datetime.datetime.now()} {text}"


def test():
    """
                 +----> Task-2 ---->|
    Task-1 ----->|                  |-----> Task-4  ---->  Task-5 ----->|
                 +----> Task-3 ---->|                                   |
                 |                                                      |
                 +----> Task-6 ---------------------------------------->|

    source  target  weight
    Start   Task-1  1
    Task-1  Task-2  1
    Task-1  Task-3  1
    Task-1  Task-6  1
    Task-2  Task-4  1
    task-3  Task-4  1
    Task-4  Task-5  1
    Task-5  Stop    1
    Task-6  Stop    1
    """
    # d = {
    #     'source': ['Start', 'Task-1', 'Task-1', 'Task-1', 'Task-2', 'Task-3', 'Task-4', 'Task-5', 'Task-6'],
    #     'target': ['Task-1', 'Task-2', 'Task-3', 'Task-6', 'Task-4', 'Task-4', 'Task-5', 'Stop', 'Stop'],
    #     'weight': [1,1,1,1,1,1,1,1,1],
    # }
    # df = pandas.DataFrame(data=d)
    # G = networkx.from_pandas_edgelist(df, source="source", target="target", edge_attr="weight")
    # networkx.draw(G)
    # plt.draw()

    # network = Network(notebook=True)
    # network.from_nx(G)
    # print("Creating network graph")
    # network.show("example.html")

    jc = JobController()
    jc.add_tasks(
        [
            Task("Task-1")
                .command("os.popen('dir').read()"),
            Task("Task-2")
                .command("os.system('python -m dosomething')")
                .wait_for("Task-1"),
            Task("Task-3")
                .command("import os")
                .wait_for("Task-1"),
            Task("Task-4")
                .command("")
                .wait_for("Task-2")
                .wait_for("Task-3"),
            Task("Task-5")
                .command("")
                .wait_for("Task-4")
                .ignore_fail_for(["Task-4"])
                .ignore_skip_for(["Task-4"]),
            Task("Task-6")
                .command("")
                .wait_for("Task-1"),
        ]
    )
    jc.start()


if __name__ == "__main__":
    test()
