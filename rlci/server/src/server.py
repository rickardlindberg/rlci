import asyncio
import json
import sys
import db

class Server:

    def __init__(self, db):
        self.db = db
        self.tasks = []

    def serve_forever(self):
        asyncio.run(self.server())

    async def server(self):
        await self.db.init()
        server = await asyncio.start_server(
            self.handle_request,
            host="localhost",
            port=9000
        )
        print("listening on port 9000")
        sys.stdout.flush()
        async with server:
            await server.serve_forever()

    async def handle_request(self, reader, writer):
        request_data = await reader.readline()
        try:
            request = json.loads(request_data)
            if request["message"] == "store_pipelines":
                response = {
                    "status": "ok",
                    "pipeline_ids": await self.db.store_pipelines(request["payload"])
                }
            elif request["message"] == "trigger":
                response = {
                    "status": "ok",
                    "execution_ids": await self.trigger(request["payload"])
                }
            elif request["message"] == "get_pipeline":
                response = {
                    "status": "ok",
                    "pipeline": await self.db.get_pipeline(request["pipeline_id"])
                }
            elif request["message"] == "get_execution":
                response = {
                    "status": "ok",
                    "execution": await self.db.get_execution(request["execution_id"])
                }
            elif request["message"] == "get_logs":
                response = {
                    "status": "ok",
                    "logs": await self.db.get_logs(request["logs_id"])
                }
            else:
                raise ValueError(f"Unknown message {request['message']}")
        except Exception as e:
            response = {"status": "error", "message": str(e)}
        writer.write(json.dumps(response).encode("utf-8"))
        writer.write(b"\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

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
        await self.start_process(
            execution["stages"][stage_id]["ast"],
            args,
            execution["stages"][stage_id]["logs"]
        )
        await self.db.modify_execution_done(execution_id)

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

    def trigger_matches(self, trigger, values):
        for key, value in trigger.items():
            if key not in values or values[key] != value:
                return False
        return True

if __name__ == "__main__":
    Server(db.create()).serve_forever()
