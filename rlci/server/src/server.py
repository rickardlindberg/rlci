import asyncio
import json
import sys
import uuid

class InMemoryObjectStore:

    def __init__(self):
        self.objects = {}

    def modify_object(self, name, fn):
        fn(self.objects[name])

    def read_object(self, name):
        return self.objects[name]

    def create_object(self, contents, name=None):
        if name is None:
            name = uuid.uuid4().hex
        self.objects[name] = contents
        return name

class PipelineDB:

    def __init__(self, db):
        self.db = db
        self.db.create_object({"pipelines": {}}, "index")

    def store_pipelines(self, pipelines):
        return [
            self.store_pipeline(pipeline[1]["name"], pipeline[2:])
            for pipeline in pipelines
        ]

    def get_pipeline(self, pipeline_id):
        return self.db.read_object(pipeline_id)

    def store_pipeline(self, name, pipeline):
        pipeline_id = self.db.create_object({"def": pipeline, "executions": []})
        self.db.modify_object("index", lambda index: index["pipelines"].__setitem__(
            "name",
            self.db.create_object({"instances": [pipeline_id]})
        ))
        return pipeline_id

    def trigger(self, values):
        executions = []
        for pipeline_id in self.db.read_object("index")["pipelines"].values():
            foo = self.db.read_object(pipeline_id)["instances"][0]
            for ast in self.db.read_object(foo)["def"]:
                if ast[0] == "Node":
                    for trigger in ast[2]["triggers"]:
                        if self.trigger_matches(trigger, values):
                            y = self.create_execution()
                            executions.append(y)
                            self.db.modify_object(foo, lambda pipeline:
                                pipeline["executions"].append(y)
                            )
        return executions

    def create_execution(self):
        return self.db.create_object({
        })

    def trigger_matches(self, trigger, values):
        for key, value in trigger.items():
            if key not in values or values[key] != value:
                return False
        return True

if __name__ == "__main__":
    db = PipelineDB(InMemoryObjectStore())
    async def handle_request(reader, writer):
        request_data = await reader.readline()
        try:
            request = json.loads(request_data)
            if request["message"] == "store_pipelines":
                response = {
                    "status": "ok",
                    "ids": db.store_pipelines(request["payload"])
                }
            elif request["message"] == "trigger":
                response = {
                    "status": "ok",
                    "executions": db.trigger(request["payload"])
                }
            elif request["message"] == "get_pipeline":
                response = {
                    "status": "ok",
                    "pipeline": db.get_pipeline(request["pipeline_id"])
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
    async def server():
        server = await asyncio.start_server(handle_request, host="localhost", port=9000)
        print("listening on port 9000")
        sys.stdout.flush()
        async with server:
            await server.serve_forever()
    asyncio.run(server())
