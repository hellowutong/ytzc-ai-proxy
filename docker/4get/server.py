from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<!DOCTYPE html><html><head><title>4get</title></head><body><h1>4get Search</h1><p>Service is running</p></body></html>")
    
    def log_message(self, format, *args):
        pass

httpd = HTTPServer(("0.0.0.0", 80), Handler)
httpd.serve_forever()
