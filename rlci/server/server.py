import asyncio
import json
import sys

if __name__ == "__main__":
    async def handle_request(reader, writer):
        request_data = await reader.readline()
        try:
            request = json.loads(request_data)
            if request["message"] == "store_pipeline":
                response = {"status": "ok"}
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
