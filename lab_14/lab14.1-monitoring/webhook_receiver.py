from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            data = {"message": body.decode("utf-8", errors="replace")}

        print("\n========== WEBHOOK ALERT RECEIVED ==========")
        print(json.dumps(data, indent=4))
        print("============================================\n")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"received"}')

    def log_message(self, format, *args):
        pass

server = HTTPServer(("127.0.0.1", 8000), WebhookHandler)
print("Local webhook receiver running at http://127.0.0.1:8000")
print("Waiting for monitoring alerts... Press Ctrl+C to stop.")
server.serve_forever()
