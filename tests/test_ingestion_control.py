import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

from lumen_brain import AsyncLumenBrainDriver, LumenBrainDriver
from lumen_brain.constants.ingestion import BrainIngestionConnection


class IngestionControlTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.calls = []
        calls = self.calls

        class Handler(BaseHTTPRequestHandler):
            def respond(self, status, body):
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(body).encode())

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                calls.append((unquote(self.path), self.headers["BrainPAT"], self.headers["X-Brain-ID"], body))
                self.respond(202, {"task_id": "task:1", "status": "cancelling", **body})

            def do_GET(self):
                calls.append((unquote(self.path), self.headers["BrainPAT"], self.headers["X-Brain-ID"]))
                self.respond(200, {"task_id": "task:1", "status": "cancelled"})

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        self.connection = BrainIngestionConnection(
            f"http://127.0.0.1:{server.server_port}", "test-brain", "test-token"
        )

    async def test_sync_and_async_cancel_and_poll(self):
        sync = LumenBrainDriver("unused", ingestion=self.connection)
        self.assertEqual(sync.cancel_ingestion("task:1", "keep_saved")["status"], "cancelling")
        self.assertEqual(sync.get_ingestion_task("task:1")["status"], "cancelled")
        async_driver = AsyncLumenBrainDriver("unused", ingestion=self.connection)
        self.assertEqual((await async_driver.cancel_ingestion("task:1", "rollback"))["status"], "cancelling")
        self.assertEqual((await async_driver.get_ingestion_task("task:1"))["status"], "cancelled")
        self.assertEqual(self.calls, [
            ("/tasks/task:1/cancel", "test-token", "test-brain", {"mode": "keep_saved"}),
            ("/tasks/task:1", "test-token", "test-brain"),
            ("/tasks/task:1/cancel", "test-token", "test-brain", {"mode": "rollback"}),
            ("/tasks/task:1", "test-token", "test-brain"),
        ])
