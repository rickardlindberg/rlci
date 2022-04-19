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

    async def create_execution(self, pipeline_id, execution):
        execution_id = await self.store.create_object(execution)
        await self.store.modify_object(pipeline_id, lambda pipeline:
            pipeline["execution_ids"].append(execution_id)
        )
        return execution_id

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
                            execution_ids.append(await self.db.create_execution(pipeline_id, {
                                "processes": [
                                    {
                                        "stage": ast[1],
                                        "args": values
                                    }
                                ]
                            }))
        return execution_ids

    def trigger_matches(self, trigger, values):
        for key, value in trigger.items():
            if key not in values or values[key] != value:
                return False
        return True

if __name__ == "__main__":
    Server(PipelineDB(InMemoryObjectStore())).serve_forever()
