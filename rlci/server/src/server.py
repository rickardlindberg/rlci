import asyncio
import json
import sys
import uuid

class DB:

    def __init__(self):
        self.objects = {"index": {"pipelines": {}}}

    def store_pipelines(self, pipelines):
        return [
            self.store_pipeline(pipeline[1]["name"], pipeline[2:])
            for pipeline in pipelines
        ]

    def get_pipeline(self, pipeline_id):
        return self.read_object(pipeline_id)

    def store_pipeline(self, name, pipeline):
        pipeline_id = self.create_object({"def": pipeline, "executions": []})
        self.modify_object("index", lambda index: index["pipelines"].__setitem__(
            "name",
            self.create_object({"instances": [pipeline_id]})
        ))
        return pipeline_id

    def trigger(self, values):
        executions = []
        for pipeline_id in self.read_object("index")["pipelines"].values():
            foo = self.read_object(pipeline_id)["instances"][0]
            for ast in self.read_object(foo)["def"]:
                if ast[0] == "Node":
                    for trigger in ast[2]["triggers"]:
                        if self.trigger_matches(trigger, values):
                            y = self.create_execution()
                            executions.append(y)
                            self.modify_object(foo, lambda pipeline:
                                pipeline["executions"].append(y)
                            )
        return executions

    def create_execution(self):
        return self.create_object({
        })

    def trigger_matches(self, trigger, values):
        for key, value in trigger.items():
            if key not in values or values[key] != value:
                return False
        return True

    def modify_object(self, name, fn):
        fn(self.objects[name])

    def read_object(self, name):
        return self.objects[name]

    def create_object(self, contents):
        new_id = uuid.uuid4().hex
        self.objects[new_id] = contents
        return new_id

if __name__ == "__main__":
    db = DB()
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
