import asyncio
import contextlib
import json
import os
import subprocess
import sys
import time
import unittest

TOOL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "tool")
sys.path.insert(0, TOOL_DIR)
import tool

class AnyCapture:

    def __eq__(self, other):
        self.value = other
        return True

class TestServer(unittest.TestCase):

    maxDiff = 10000

    def test_server(self):
        any_capture = AnyCapture()
        with self.server() as send:
            self.assertEqual(send({
                "message": "store_pipelines",
                "payload": tool.compile_pipeline_file("""
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
                {"status": "ok", "pipeline_ids": [any_capture]}
            )
            pipeline_id = any_capture.value
            self.assertEqual(send({
                "message": "trigger",
                "payload": {"type": "test", "arg": 99}
            }),
                {"status": "ok", "execution_ids": [any_capture]}
            )
            execution_id = any_capture.value
            self.assertEqual(send({
                "message": "get_pipeline",
                "pipeline_id": pipeline_id
            }),
                {"status": "ok", "pipeline": {
                    "definition": any_capture,
                    "execution_ids": [execution_id]
                }}
            )
            for i in range(5):
                self.assertEqual(send({
                    "message": "get_execution",
                    "execution_id": execution_id
                }),
                    {"status": "ok", "execution": any_capture}
                )
                execution = any_capture.value
                if execution["status"] == "done":
                    logs_0_capture = AnyCapture()
                    logs_1_capture = AnyCapture()
                    self.assertEqual(execution, {
                        "status": "done",
                        "stages": {
                            "0": {
                                "ast": any_capture,
                                "status": "running",
                                "input": {"type": "test", "arg": 99},
                                "output": {},
                                "logs": logs_0_capture,
                                "children": ["1"],
                                "parents": [],
                            },
                            "1": {
                                "ast": any_capture,
                                "status": "waiting",
                                "input": {},
                                "output": {},
                                "logs": logs_1_capture,
                                "children": [],
                                "parents": ["0"],
                            },
                        },
                    })
                    self.assertEqual(send({
                        "message": "get_logs",
                        "logs_id": logs_0_capture.value,
                    }), {
                        "status": "ok",
                        "logs": {
                            "lines": [
                                ["Log", "stdout", "99"],
                                ["Result", "success", {}],
                            ]
                        }
                    })
                    self.assertEqual(send({
                        "message": "get_logs",
                        "logs_id": logs_1_capture.value,
                    }), {
                        "status": "ok",
                        "logs": {
                            "lines": [
                            ]
                        }
                    })
                    break
                time.sleep(0.1*i)
            else:
                self.fail("Timed out waiting for execution to finish")


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
            stdout=subprocess.PIPE,
        ) as process:
            process.stdout.readline()
            try:
                yield lambda x: asyncio.run(communicate(x))
            finally:
                process.kill()

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    unittest.main(verbosity=2)
