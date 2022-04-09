#!/usr/bin/env python

import asyncio
import contextlib
import json
import os
import subprocess
import unittest
import tool

class TestServer(unittest.TestCase):

    def test_server(self):
        with self.server() as send:
            x = tool.compile_pipeline("""
                pipeline {
                    stage {
                        sh "echo 1"
                    }
                    stage {
                        sh "echo 2"
                    }
                }
            """)
            # 1. compile pipeline
            # 2. message: store pipeline
            # 3. message: trigger
            # 4. message: get pipeline execution
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
            await writer.drain()
            response = await reader.readline()
            writer.close()
            await writer.wait_closed()
            return json.loads(response)
        with subprocess.Popen(["python", "server.py"]) as process:
            try:
                yield lambda x: asyncio.run(communicate(x))
            finally:
                process.kill()

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    unittest.main(verbosity=2)
