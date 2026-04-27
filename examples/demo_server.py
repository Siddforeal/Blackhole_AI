from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class DemoHandler(BaseHTTPRequestHandler):
    def _json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/users/me":
            self._json(200, {
                "id": 1,
                "email": "demo-user@example.com",
                "role": "researcher",
                "account_id": 1001
            })
            return

        if self.path == "/api/admin/settings":
            self._json(403, {
                "error": "Forbidden"
            })
            return

        self._json(404, {
            "error": "Not found"
        })


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8765), DemoHandler)
    print("Demo API running at http://127.0.0.1:8765")
    server.serve_forever()
