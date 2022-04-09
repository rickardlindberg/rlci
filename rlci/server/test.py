#!/usr/bin/env python

import asyncio
import contextlib
import json
import os
import subprocess
import unittest

class TestServer(unittest.TestCase):

    def test_server(self):
        with self.server() as send:
            self.assertEqual(
                send({"message": "hello"}),
                {"message": "hello"}
            )

    @contextlib.contextmanager
    def server(self):
        async def communicate(request):
            await asyncio.sleep(0.5)
            reader, writer = await asyncio.open_connection("localhost", 9000)
            writer.write(json.dumps(request).encode("utf-8"))
            writer.write(b"\n")
            response = await reader.readline()
            return json.loads(response)
        with subprocess.Popen(["python", "server.py"]) as process:
            try:
                yield lambda x: asyncio.run(communicate(x))
            finally:
                process.kill()

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    unittest.main(verbosity=2)
