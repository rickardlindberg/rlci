import asyncio
import json
import sys
import uuid

class DB:

    def __init__(self):
        self.pipelines = {}
        self.objects = {}

    def store_pipelines(self, pipelines):
        return [
            self.store_pipeline(pipeline[1]["name"], pipeline[2:])
            for pipeline in pipelines
        ]

    def store_pipeline(self, name, pipeline):
        pipeline_id = self.create_object(pipeline)
        if name not in self.pipelines:
            self.pipelines["name"] = self.create_object({
                "instances": [pipeline_id]
            })
        else:
            raise NotImplementedError("store existing pipeline")
        return pipeline_id

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
                response = {"status": "ok"}
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
