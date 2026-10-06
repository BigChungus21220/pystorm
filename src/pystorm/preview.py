import json
import urllib.request
import urllib.parse
import urllib.error
import os
import sys
import subprocess
import socket
import time
import platform
from typing import Literal

HOST = "127.0.0.1"
PORT = 8000
BASE_URL = f"http://{HOST}:{PORT}"

def checkStatus() -> bool:
    server_up = False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        server_up = (s.connect_ex((HOST, PORT)) == 0)
        
    return server_up

def startServer(timeout: float | None | Literal["default"] = None):
    server_up = False
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(script_dir, "server.py")
    
    kwargs = {}
    if platform.system() == 'Windows':
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        kwargs['creationflags'] = 0x00000008 | 0x00000200
    else:
        kwargs['start_new_session'] = True
        
    process_cmd = [sys.executable, server_path]
    
    proc = subprocess.Popen(process_cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)
    print(f"Server started on PID: {proc.pid}")
    
    for _ in range(10):
        time.sleep(0.5)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((HOST, PORT)) == 0:
                server_up = True
                break
                
    if not server_up:
        raise ConnectionError(f"Could not connect to or start server at {BASE_URL}")
    
    if timeout != "default":
        setTimeout(timeout)
        
    return BASE_URL


def sendReq(url: str, method: str, content_type: str | None = None, data: bytes | None = None):
    req = urllib.request.Request(url, data=data, method=method)
    if content_type is not None:
        req.add_header('Content-Type', content_type)
    req.add_header('Content-Length', str(len(data) if data is not None else 0))
    urllib.request.urlopen(req)
    
    
def stopServer():
    sendReq(
        url = f"{BASE_URL}/shutdown",
        method = "POST"
    )
    
def setTimeout(timeout: float | None):
    if timeout is None:
        timeout = 1000000
    if checkStatus():
        try:
            sendReq(
                url = f"{BASE_URL}/timeout",
                data = urllib.parse.urlencode({'timeout': timeout*60.0}).encode('utf-8'),
                method = 'POST',
                content_type = 'application/x-www-form-urlencoded'
            )
        except (urllib.error.URLError, ConnectionError) as e:
            print(f"Failed to communicate with the server: {e}")
    
def setView(identifier: str):
    identifier = identifier.replace(":", "~")
    if checkStatus():
        try:
            sendReq(
                url = f"{BASE_URL}/view",
                data = urllib.parse.urlencode({'effect': identifier}).encode('utf-8'),
                method = 'POST',
                content_type = 'application/x-www-form-urlencoded'
            )
        except (urllib.error.URLError, ConnectionError) as e:
            print(f"Failed to communicate with the server: {e}")

def previewEffect(particle: dict, texture: bytes, change_view: bool = True, start_server: bool = True):
    try:
        name: str = particle.get("particle_effect",{}).get("description",{}).get("identifier")
        name = name.replace(":", "~")
    except json.JSONDecodeError:
        print("Could not display effect. Parse error.")
        return
    if not isinstance(name, str):
        print("Could not display effect. Identifier not found.")
        return

    try:
        if not checkStatus():
            if start_server:
                print("Preview server not responding. Starting local server...")
                startServer()
            else:
                print("Cannot preview effect. Preview server not responding.")
                return
        
        
        safe_name = urllib.parse.quote(name, safe='')
        
        sendReq(
            url = f"{BASE_URL}/{safe_name}.particle.json",
            data = json.dumps(particle).encode('utf-8'),
            method = 'PUT',
            content_type = 'application/json'
        )
        
        sendReq(
            url = f"{BASE_URL}/{safe_name}.png",
            data = texture,
            method = 'PUT',
            content_type = 'image/png'
        )

        if (change_view):
            sendReq(
                url = f"{BASE_URL}/view",
                data = urllib.parse.urlencode({'effect': name}).encode('utf-8'),
                method = 'POST',
                content_type = 'application/x-www-form-urlencoded'
            )

        print(f"Previewing effect on {BASE_URL}/")

    except (urllib.error.URLError, ConnectionError) as e:
        print(f"Failed to communicate with the server: {e}")
        
def queryPID() -> int:
    if checkStatus():
        try:
            url = f"{BASE_URL}/pid.txt"
            with urllib.request.urlopen(url) as response:
                pid_string = response.read().decode('utf-8').strip()
                pid = int(pid_string)
            return pid
        except (urllib.error.URLError, ConnectionError) as e:
            print(f"Failed to communicate with the server: {e}")
            return 0
    else:
        return 0