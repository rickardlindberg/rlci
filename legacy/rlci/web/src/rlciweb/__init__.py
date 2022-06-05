import asyncio
import json
import os

from flask import Flask, render_template

import ipc

app = Flask(__name__)

server = ipc.Client(
    os.environ["RLCI_SERVER_ADDRESS"],
    int(os.environ["RLCI_SERVER_PORT"])
)

@app.route("/")
def main():
    response = server.send({
        "message": "get_pipelines"
    })
    assert response["status"] == "ok"
    return render_template("main.html", pipelines=response["pipelines"])
