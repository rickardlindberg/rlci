import asyncio
import json
import sys

import db
import ipc

class StageExecutioner:

    def __init__(self, db):
        self.db = db

    async def start_process(self, ast, args, logs_id):
        cmd_args = []
        for key, value in args.items():
            cmd_args.append(f"{key}={value}")
        process = await asyncio.create_subprocess_exec(
            sys.executable, "../../tool/tool.py", "run", *cmd_args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate(json.dumps(ast).encode("utf-8"))
        for line in stdout.splitlines():
            await self.db.add_log(logs_id, json.loads(line))
        await process.wait()

class JobController:

    def __init__(self, db, stage_executioner):
        self.db = db
        self.tasks = []
        self.stage_executioner = stage_executioner

    async def trigger(self, values):
        execution_ids = []
        for (pipeline_id, pipeline) in await self.db.get_active_pipelines():
            for ast in pipeline["definition"]:
                if ast[0] == "Node":
                    for trigger in ast[2]["triggers"]:
                        if self.trigger_matches(trigger, values):
                            execution_id = await self.db.store_execution(
                                pipeline_id,
                                await self.create_execution(pipeline)
                            )
                            execution_ids.append(execution_id)
                            task = asyncio.create_task(self.execute_stage(execution_id, str(ast[1]), values))
                            self.tasks.append(task)
                            task.add_done_callback(lambda x: self.tasks.remove(x))
        return execution_ids

    def trigger_matches(self, trigger, values):
        for key, value in trigger.items():
            if key not in values or values[key] != value:
                return False
        return True

    async def create_execution(self, pipeline):
        stages = {}
        for ast in pipeline["definition"]:
            if ast[0] == "Node":
                stages[str(ast[1])] = {
                    "ast": ast[3],
                    "status": "waiting",
                    "input": {},
                    "output": {},
                    "logs": await self.db.store_logs({"lines": []}),
                    "children": [],
                    "parents": [],
                }
            elif ast[0] == "Link":
                stages[str(ast[1])]["children"].append(str(ast[2]))
                stages[str(ast[2])]["parents"].append(str(ast[1]))
        return {
            "status": "running",
            "stages": stages,
        }

    async def execute_stage(self, execution_id, stage_id, args):
        execution = await self.db.modify_execution_start(execution_id, stage_id, args)
        await self.stage_executioner.start_process(
            execution["stages"][stage_id]["ast"],
            args,
            execution["stages"][stage_id]["logs"]
        )
        await self.db.modify_execution_done(execution_id)

class Server(ipc.Server):

    def __init__(self, db):
        ipc.Server.__init__(self, "localhost", 9000)
        self.db = db
        self.job_controller = JobController(db, StageExecutioner(db))

    async def before_start(self):
        await self.db.init()

    async def store_pipelines(self, request):
        return {
            "pipeline_ids": await self.db.store_pipelines(request["payload"])
        }

    async def trigger(self, request):
        return {
            "execution_ids": await self.job_controller.trigger(request["payload"])
        }

    async def get_pipelines(self, request):
        return {
            "pipelines": await self.db.get_pipelines()
        }

    async def get_pipeline(self, request):
        return {
            "pipeline": await self.db.get_pipeline(request["pipeline_id"])
        }

    async def get_execution(self, request):
        return {
            "execution": await self.db.get_execution(request["execution_id"])
        }

    async def get_logs(self, request):
        return {
            "logs": await self.db.get_logs(request["logs_id"])
        }

if __name__ == "__main__":
    Server(db.create()).start()
