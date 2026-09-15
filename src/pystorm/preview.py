from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

def previewEffect(particle, texture):
    # map requests for particle / texture to particle / texture args
    
    current_dir = Path(__file__).resolve().parent
    
    class RequestHandler(SimpleHTTPRequestHandler):

        def do_GET(self):
            allow_list = ["/main.js", "/molang.umd.js", "/wintersky.umd.js", "/OrbitControls.js", "/three.min.js", "/tinycolor-min.js"]
            content_type = ''
            data = bytes()
            good = False
            
            if self.path == "/effect.particle.json":
                good = True
                content_type = 'application/json; charset=utf-8'
                data = particle.encode('utf-8')
                
            elif self.path == "/texture.png":
                good = True
                content_type = 'image/png'
                data = texture
                
            elif self.path in ["", ".", "/", "/index", "/index.html", "index", "index.html"]:
                with open(current_dir / "webapp/index.html", "r", encoding="utf-8") as f:
                    index = f.read()
                
                good = True
                content_type = 'text/html; charset=utf-8'
                data = index.encode('utf-8')
                
            elif self.path in allow_list:
                with open(current_dir / "webapp" / self.path[1:], "r", encoding="utf-8") as f:
                    file = f.read()
                
                good = True
                content_type = 'text/javascript; charset=utf-8'
                data = file.encode('utf-8')
                
            if good:
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
    
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, RequestHandler)
    print("Serving HTTP on http://localhost:8000 ...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()