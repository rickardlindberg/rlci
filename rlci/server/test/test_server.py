import asyncio
import contextlib
import json
import os
import subprocess
import sys
import unittest

TOOL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "tool")
sys.path.insert(0, TOOL_DIR)
import tool

class TestServer(unittest.TestCase):

    def test_server(self):
        with self.server() as send:
            self.assertEqual(send({
                "message": "store_pipeline",
                "payload": tool.compile_pipeline("""
                    pipeline {
                        stage {
                            trigger type="test"
                            sh "echo ${arg}"
                        }
                        stage {
                            sh "echo child"
                        }
                    }
                """)
            }),
                {"status": "ok"}
            )
            self.assertEqual(send({
                "message": "trigger",
                "payload": {"type": "test", "arg": 99}
            }),
                {"status": "ok"}
            )
            # 4. message: get pipeline execution

    @contextlib.contextmanager
    def server(self):
        async def communicate(request):
            reader, writer = await asyncio.open_connection("localhost", 9000)
            writer.write(json.dumps(request).encode("utf-8"))
            writer.write(b"\n")
            await writer.drain()
            response = await reader.readline()
            writer.close()
            await writer.wait_closed()
            return json.loads(response)
        with subprocess.Popen(
            [sys.executable, "../src/server.py"],
            stdout=subprocess.PIPE
        ) as process:
            process.stdout.readline()
            try:
                yield lambda x: asyncio.run(communicate(x))
            finally:
                process.kill()

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    unittest.main(verbosity=2)
