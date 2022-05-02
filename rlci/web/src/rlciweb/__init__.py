import asyncio
import json
import os

from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template("main.html", status=talk_to_server({"message":
    "status"}))

def talk_to_server(request):
    async def communicate():
        reader, writer = await asyncio.open_connection(
            os.environ["RLCI_SERVER_ADDRESS"],
            int(os.environ["RLCI_SERVER_PORT"])
        )
        writer.write(json.dumps(request).encode("utf-8"))
        writer.write(b"\n")
        await writer.drain()
        response = await reader.readline()
        writer.close()
        await writer.wait_closed()
        return json.loads(response)
    return asyncio.run(communicate())
