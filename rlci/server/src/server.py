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

    async def get_pipeline(self, pipeline_id):
        return await self.store.read_object(pipeline_id)

    async def get_execution(self, execution_id):
        return await self.store.read_object(execution_id)

    async def store_pipeline(self, name, pipeline):
        pipeline_id = await self.store.create_object({"def": pipeline, "executions": []})
        foo = await self.store.create_object({"instances": [pipeline_id]})
        await self.store.modify_object("index", lambda index:
            index["pipelines"].__setitem__(
                "name",
                foo
            )
        )
        return pipeline_id

    async def trigger(self, values):
        executions = []
        for pipeline_id in (await self.store.read_object("index"))["pipelines"].values():
            foo = (await self.store.read_object(pipeline_id))["instances"][0]
            for ast in (await self.store.read_object(foo))["def"]:
                if ast[0] == "Node":
                    for trigger in ast[2]["triggers"]:
                        if self.trigger_matches(trigger, values):
                            y = await self.create_execution()
                            executions.append(y)
                            await self.store.modify_object(foo, lambda pipeline:
                                pipeline["executions"].append(y)
                            )
        return executions

    def trigger_matches(self, trigger, values):
        for key, value in trigger.items():
            if key not in values or values[key] != value:
                return False
        return True

    async def create_execution(self):
        return await self.store.create_object({
        })

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
                    "ids": await self.db.store_pipelines(request["payload"])
                }
            elif request["message"] == "trigger":
                response = {
                    "status": "ok",
                    "executions": await self.db.trigger(request["payload"])
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

if __name__ == "__main__":
    Server(PipelineDB(InMemoryObjectStore())).serve_forever()
