import asyncio
import json
import sys
import uuid

class InMemoryObjectStore:

    def __init__(self):
        self.objects = {}

    async def create_object(self, contents, name=None):
        if name is None:
            name = uuid.uuid4().hex
        self.objects[name] = contents
        return name

    async def modify_object(self, name, fn):
        fn(self.objects[name])
        return self.objects[name]

    async def read_object(self, name):
        return self.objects[name]

class PipelineDB:

    def __init__(self, store):
        self.store = store

    async def init(self):
        await self.store.create_object({"pipelines": {}}, "index")

    async def store_pipelines(self, pipelines):
        return [
            await self.store_pipeline(pipeline[1]["name"], pipeline[2:])
            for pipeline in pipelines
        ]

    async def get_active_pipelines(self):
        active_pipelines = []
        index = await self.store.read_object("index")
        for pipeline_id in index["pipelines"].values():
            pipeline = await self.store.read_object(pipeline_id)
            active_id = pipeline["versions"][0]
            active_pipeline = await self.store.read_object(active_id)
            active_pipelines.append((active_id, active_pipeline))
        return active_pipelines

    async def store_execution(self, pipeline_id, execution):
        execution_id = await self.store.create_object(execution)
        await self.store.modify_object(pipeline_id, lambda pipeline:
            pipeline["execution_ids"].append(execution_id)
        )
        return execution_id

    async def modify_execution_done(self, execution_id):
        def modify(execution):
            execution["status"] = "done"
        return await self.store.modify_object(execution_id, modify)

    async def modify_execution_start(self, execution_id, stage_id, args):
        def modify(execution):
            execution["stages"][stage_id]["status"] = "running"
            execution["stages"][stage_id]["input"] = args
        return await self.store.modify_object(execution_id, modify)

    async def add_log(self, logs_id, line):
        def modify(logs):
            logs["lines"].append(line)
        return await self.store.modify_object(logs_id, modify)

    async def store_logs(self, logs):
        return await self.store.create_object(logs)

    async def get_logs(self, logs_id):
        return await self.store.read_object(logs_id)

    async def get_pipeline(self, pipeline_id):
        return await self.store.read_object(pipeline_id)

    async def get_execution(self, execution_id):
        return await self.store.read_object(execution_id)

    async def store_pipeline(self, name, pipeline):
        pipeline_id = await self.store.create_object({
            "definition": pipeline,
            "execution_ids": []
        })
        foo = await self.store.create_object({"versions": [pipeline_id]})
        await self.store.modify_object("index", lambda index:
            index["pipelines"].__setitem__(
                "name",
                foo
            )
        )
        return pipeline_id

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
    Server(PipelineDB(InMemoryObjectStore())).serve_forever()
