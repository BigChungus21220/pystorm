from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import urllib.parse
from datetime import datetime, timezone
import socket
import sys
import threading
import queue
import os

PORT = 8000
INACTIVITY_TIMEOUT = 10*60
APP_DIR = Path(__file__).resolve().parent / "webapp"

clients = []

particle_ext = ".particle.json"
texture_ext = ".png"

particles: dict[str, bytes] = {}
textures: dict[str, bytes] = {}
updates: dict[str, str] = {}
active: dict[str, str] = {"effect": "_placeholder"}

def notify_clients(event_type, payload):
    message = f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"
    for client_queue in clients:
        client_queue.put(message)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        global particles, textures, updates, active
        super().__init__(request, client_address, server, directory=APP_DIR)
        
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        query_parameters = urllib.parse.parse_qs(parsed_url.query)
        
        # SSE endpoint
        if parsed_url.path == "/events":
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            
            client_queue = queue.Queue()
            clients.append(client_queue)
            
            try:
                # Keep connection alive and wait for messages
                while True:
                    msg = client_queue.get()
                    self.wfile.write(msg.encode('utf-8'))
                    self.wfile.flush()
            except Exception:
                # Client disconnected
                pass
            finally:
                if client_queue in clients:
                    clients.remove(client_queue)
            return
        
        # active effect
        if parsed_url.path == "/active.json":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            self.wfile.write(json.dumps(active).encode("utf-8"))
            return
        
        # effect directory
        if parsed_url.path == "/effects.json":
            effects = {name: {
                "updated": updates[name]
            } for name in particles.keys()}
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
                
            self.wfile.write(json.dumps(effects).encode("utf-8"))
            return
        
        if parsed_url.path == "/pid.txt":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
                
            self.wfile.write(str(os.getpid()).encode('utf-8'))
            return
        
        # effect / texture requests
        is_particle = parsed_url.path.endswith(particle_ext)
        is_texture = parsed_url.path.endswith(texture_ext)
        
        if is_particle or is_texture:
            data = b''
            
            if is_particle:
                file_name = parsed_url.path[1:-len(particle_ext)]
                content_type = "application/json"
                success = file_name in particles
                if success:
                    data = particles[file_name]
            else:
                file_name = parsed_url.path[1:-len(texture_ext)]
                content_type = "image/png"
                success = file_name in textures
                if success:
                    data = textures[file_name]
            
            if success:
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.end_headers()
                    
                self.wfile.write(data)
            else:
                # Go to fallback file or try in files
                if "fallback" in query_parameters:
                    self.path = query_parameters["fallback"][0]
                super().do_GET()
            return
        
        # normal file requests
        super().do_GET()
            
    def do_PUT(self):
        is_particle = self.path.endswith(particle_ext)
        is_texture = self.path.endswith(texture_ext)
        if is_particle or is_texture:
            if is_particle:
                file_name = self.path[1:-len(particle_ext)]
                print(f"Received PUT for particle '{file_name}'")
            else:
                file_name = self.path[1:-len(texture_ext)]
                print(f"Received PUT for texture '{file_name}'")
            
            content_length = int(self.headers['Content-Length'])
            
            data = self.rfile.read(content_length)
            
            update = False
            
            if is_particle:
                if particles.get(file_name) != data:
                    updates[file_name] = datetime.now(timezone.utc).isoformat()
                    update = True
                    
                particles[file_name] = data
            else:
                if file_name in particles and textures.get(file_name) != data:
                    updates[file_name] = datetime.now(timezone.utc).isoformat()
                    update = True
                
                textures[file_name] = data
                
            #if update:
            if True:
                notify_clients("file_update", {
                    "effect": file_name,
                    "type": "particle" if is_particle else "texture",
                    "timestamp": updates[file_name]
                })
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
        else:
            self.send_error(400, "Bad Request. Expected .particle.json or .png file")
            
    def do_POST(self):
        global active
        if self.path == "/shutdown":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "shutting down"}).encode('utf-8'))
            
            threading.Thread(target=self.server.server_close, daemon=True).start()
            return
        
        elif self.path == "/view":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            parsed_data = urllib.parse.parse_qs(body)
            
            if 'effect' in parsed_data:
                effect_name = parsed_data['effect'][0]
                
                active = {
                    "effect": effect_name
                }
                
                notify_clients("view_change", active)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "effect": effect_name}).encode('utf-8'))
            else:
                self.send_error(400, "Missing 'effect' parameter")
        
        elif self.path == "/timeout":
            
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            parsed_data = urllib.parse.parse_qs(body)
            
            if 'timeout' in parsed_data:
                timeout = float(parsed_data["timeout"][0])
                self.server.timeout = timeout
                    
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "timeout": timeout}).encode('utf-8'))
            else:
                self.send_error(400, "Missing 'timeout' parameter")
                
        else:
            self.send_error(404, "Not Found")
            

class Server(ThreadingHTTPServer):
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate: bool = True) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.timeout = INACTIVITY_TIMEOUT
        
    def handle_timeout(self) -> None:
        print(f"\nNo requests received for {INACTIVITY_TIMEOUT} seconds. Stopping server...")
        self.server_close()


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    if s.connect_ex(('127.0.0.1', PORT)) == 0:
        print("Cannot open server, port {PORT} is in use", file=sys.stderr)
        exit(1)

with Server(("127.0.0.1", PORT), Handler) as server:
    server.timeout = INACTIVITY_TIMEOUT
    
    print(f"Server running on http://127.0.0.1:{PORT}/")
    try:
        while server:
            try:
                server.handle_request()
            except KeyboardInterrupt:
                print("\nStopping server.")
                break
    finally:
        server.server_close()
        print("Server cleanly shut down.")