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

import asyncio
import random


class Task:

    def __init__(self, name):
        self._name = name
        self._wait_for = []

    @property
    def name(self):
        return self._name

    @property
    def wait(self):
        return self._wait_for

    @wait.setter
    def wait(self, value):
        self._wait_for = value

    def __repr__(self):
        return f"<Task {self._name} at {hex(id(self))}>"

    def wait_for(self, task_name):
        self._wait_for.append(task_name)
        return self

    async def run(self, callback):
        time_to_sleep = random.randint(1, 5)
        await asyncio.sleep(5)
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
        print("[JOBCTRL] Job started  :")
        while len(self._waiting_tasks) + len(self._running_tasks) + len(self._start_tasks) > 0:
            self._process_tasks()
        print("[JOBCTRL] Job finsished:")

    def _process_tasks(self):
        self._move_tasks_from_wait_queue()
        self._do_start_tasks()

    def _move_tasks_from_wait_queue(self):
        for task in self._waiting_tasks:
            if self._can_start(task):
                self._start_tasks.append(task)
        self._waiting_tasks = [task for task in self._waiting_tasks if task not in self._start_tasks]

    def _can_start(self, task):
        task.wait = list(set(task.wait).difference(set([task.name for task in self._finished_tasks])))
        return len(task.wait) == 0

    def _do_start_tasks(self):
        collector = []
        for task in self._start_tasks:
            collector.append(task)
        self._start_tasks = []
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        tasks = [new_loop.create_task(self._execute_task(task)) for task in collector]
        new_loop.run_until_complete(asyncio.wait(tasks))
        new_loop.close()

    async def _execute_task(self, task):
        print(f"[JOBCTRL] Task started : {task}")
        self._running_tasks.append(task)
        await task.run(self.task_finished)

    def task_finished(self, task):
        self._finished_tasks.append(task)
        self._running_tasks.remove(task)
        print(f"[JOBCTRL] Task finished: {task}")



def test():
    """
                   +----> Task-2 ---->|
      Task-1 ----->|                  |-----> Task-4  ---->  Task-5 ----->|
                   +----> Task-3 ---->|                                   |
                   |                                                      |
                   +----> Task-6 ---------------------------------------->|

    """
    jc = JobController()
    jc.add_tasks([
        Task("Task-1"),
        Task("Task-2").wait_for("Task-1"),
        Task("Task-3").wait_for("Task-1"),
        Task("Task-4").wait_for("Task-2").wait_for("Task-3"),
        Task("Task-5").wait_for("Task-4"),
        Task("Task-6").wait_for("Task-1"),
    ])
    jc.start()


if __name__ == "__main__":
    test()
