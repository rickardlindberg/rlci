import asyncio

if __name__ == "__main__":
    async def handle_request(reader, writer):
        request = await reader.readline()
        writer.write(request)
        await writer.drain()
        writer.close()
        await writer.wait_closed()
    async def server():
        server = await asyncio.start_server(handle_request, host="localhost", port=9000)
        async with server:
            await server.serve_forever()
    asyncio.run(server())
