import http.server
import socketserver
import os

class RedirectHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/Mussels.html')
            self.end_headers()
        else:
            super().do_GET()

directory = os.path.dirname(os.path.abspath(__file__))
PORT = 8000
os.chdir(directory)
Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("", PORT), RedirectHandler) as httpd:
    print(f"Serving at http://localhost:{PORT}")
    httpd.serve_forever()