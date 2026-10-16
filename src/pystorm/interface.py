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
from pathlib import Path
from .utils import indexFolder

HOST = "127.0.0.1"
PORT = 8000

def base_url(port = PORT):
    return f"http://{HOST}:{port}"

def sendReq(url: str, method: str, content_type: str | None = None, data: bytes | None = None) -> int:
    """Sends a request to the server. Args do what you expect (or you shouldn't be using it)"""
    req = urllib.request.Request(url, data=data, method=method)
    if content_type is not None:
        req.add_header('Content-Type', content_type)
    req.add_header('Content-Length', str(len(data) if data is not None else 0))
    return urllib.request.urlopen(req)
    

def checkStatus(port = PORT) -> str | None:
    """Returns the server base url if the server is up, else None"""
    server_up = False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        server_up = (s.connect_ex((HOST, port)) == 0)
        
    return base_url(port) if server_up else None

def startServer(timeout: float | None | Literal["default"] = None, port = PORT) -> tuple[bool, str, str | None]:
    """Starts the server if it isn't up
    
    Args:
        timeout: Optional timeout (seconds), where the server will shutdown if it is unused for that time.
        
    Returns:
       Status, message, base url, PID
    """
    if checkStatus(port): return (True, f"Server up at {base_url(port)}", base_url(port))
    
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
    
    for _ in range(10):
        time.sleep(0.5)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((HOST, port)) == 0:
                server_up = True
                break
                
    if not server_up:
        return (False, f"Could not start server at {base_url(port)}", None)
    
    if timeout != "default":
        setTimeout(timeout)
        
    return (True, f"Server started at {base_url(port)}", base_url(port))
    
    
def stopServer(port = PORT) -> tuple[bool, str]:
    """Stops the server if it is running
        
    Returns:
       Status, message
    """
    if checkStatus(port):
        sendReq(
            url = f"{base_url(port)}/shutdown",
            method = "POST"
        )
        return (True, "Server stopped")
    return (False, "Server is down")
        
    
def setTimeout(timeout: float | None, port = PORT) -> tuple[bool, str]:
    """Sets the timeout (seconds), where the server will shutdown if unused for that amount of time.
    Returns:
       Status, message
    """
    if timeout is None:
        timeout = 1000000
    if checkStatus(port):
        try:
            sendReq(
                url = f"{base_url(port)}/timeout",
                data = urllib.parse.urlencode({'timeout': timeout*60.0}).encode('utf-8'),
                method = 'POST',
                content_type = 'application/x-www-form-urlencoded'
            )
            return (True, f"Timeout set to {timeout} seconds.")
        except (urllib.error.URLError, urllib.error.HTTPError, ConnectionError) as e:
            return (False, f"Failed to communicate with the server: {e}")
    return (False, "Server is down")
    
def setView(identifier: str, port = PORT) -> tuple[bool, str]:
    """Sets the current file to preview. Accepts a minecraft identifier (`namespace:identifier`)
            
    Returns:
       Status, message
    """
    identifier = identifier.replace(":", "~")
    if checkStatus(port):
        try:
            sendReq(
                url = f"{base_url(port)}/view",
                data = urllib.parse.urlencode({'effect': identifier}).encode('utf-8'),
                method = 'POST',
                content_type = 'application/x-www-form-urlencoded'
            )
            return (True, f"Previewing effect {identifier} on {base_url(port)}")
        except (urllib.error.URLError, urllib.error.HTTPError, ConnectionError) as e:
            return (False, f"Failed to communicate with the server: {e}")
    return (False, "Server is down")

def clearEffects(port = PORT) -> tuple[bool, str]:
    """Clears all effects from the server and clients.
        
    Returns:
       Status, message
    """
    if checkStatus(port):
        try:
            sendReq(
                url = f"{base_url(port)}/clear",
                method = 'POST',
                content_type = 'application/x-www-form-urlencoded'
            )
            return (True, "Cleared all effects")
        except (urllib.error.URLError, urllib.error.HTTPError, ConnectionError) as e:
            return (False, f"Failed to communicate with the server: {e}")
    return (False, "Server is down")

def removeEffect(identifier: str, port = PORT) -> tuple[bool, str]:
    """Removes an effect from the server and client
        
    Returns:
       Status, message
    """
    identifier = identifier.replace(":", "~")
    if checkStatus(port):
        try:
            sendReq(
                url = f"{base_url(port)}/remove",
                data = urllib.parse.urlencode({'effect': identifier}).encode('utf-8'),
                method = 'POST',
                content_type = 'application/x-www-form-urlencoded'
            )
            return (True, f"Removed effect {identifier}")
        except (urllib.error.URLError, urllib.error.HTTPError, ConnectionError) as e:
            return (False, f"Failed to communicate with the server: {e}")
    return (False, "Server is down")

def previewEffect(particle: dict, texture: bytes, change_view: bool = True, start_server: bool = True, additional_data: dict | None = None, port = PORT) -> tuple[bool, str]:
    """Previews a particle effect on the local server

    Args:
        particle: The particle json to show
        texture: The texture to use
        change_view: Whether the view should be updated to this particle with this request. Defaults to True.
        start_server: Whether to start the server if it is down. Defaults to True.
        additional_data: Additional data which may be used by the client.
        
    
    Returns:
       Status, message
    """
    try:
        name: str = particle.get("particle_effect",{}).get("description",{}).get("identifier")
        name = name.replace(":", "~")
    except json.JSONDecodeError:
        return (False, "Could not display effect. Parse error.")
    if not isinstance(name, str):
        return (False, "Could not display effect. Identifier not found in particle json.")

    try:
        if not checkStatus(port):
            if start_server:
                print("Preview server not responding. Starting local server...")
                res = startServer(port)
                if not res[0]:
                    return (False, res[1])
            else:
                return (False, "Server is down")
        
        
        safe_name = urllib.parse.quote(name, safe='')
        
        sendReq(
            url = f"{base_url(port)}/{safe_name}.particle.json",
            data = json.dumps(particle).encode('utf-8'),
            method = 'PUT',
            content_type = 'application/json'
        )
        
        sendReq(
            url = f"{base_url(port)}/{safe_name}.png",
            data = texture,
            method = 'PUT',
            content_type = 'image/png'
        )
        

        sendReq(
            url = f"{base_url(port)}/{safe_name}.additional.json",
            data = json.dumps(additional_data if additional_data is not None else {}).encode('utf-8'),
            method = 'PUT',
            content_type = 'application/json'
        )

        if (change_view):
            sendReq(
                url = f"{base_url(port)}/view",
                data = urllib.parse.urlencode({'effect': name}).encode('utf-8'),
                method = 'POST',
                content_type = 'application/x-www-form-urlencoded'
            )

        return (True, f"Previewing effect {name} on {base_url(port)}/")

    except (urllib.error.URLError, urllib.error.HTTPError, ConnectionError) as e:
        return (False, f"Failed to communicate with the server: {e}")
        
def queryPID(port = PORT) -> tuple[bool, str, int | None]:
    """Returns the process id of the server process
    
    Returns:
       Status, message, pid or None
    """
    if checkStatus(port):
        try:
            url = f"{base_url(port)}/pid.txt"
            with urllib.request.urlopen(url) as response:
                pid_string = response.read().decode('utf-8').strip()
                pid = int(pid_string)
                return (True, f"Server is running on {pid}", pid)
        except (urllib.error.URLError, urllib.error.HTTPError, ConnectionError) as e:
            return (False, f"Failed to communicate with the server: {e}", None)
    else:
        return (False, "Server is down", None)
    
def galleryFromFolder(folder: Path | str, search_referenced: bool = True, port=PORT) -> tuple[bool, str]:
    """Attempts to load particles from a folder to the gallery.

    Args:
        folder: Folder to search.
        search_referenced: Whether to take into account `decription.basic_render_parameters.texture` when searching for textures.
    """
    
    loaded = 0
    for particle, texture in indexFolder(folder):
        if texture is not None:
            with Path.open(particle, 'r', encoding='utf-8') as f:
                particle_json = json.load(f)
            with Path.open(texture, 'rb') as f:
                texture_bytes = f.read()
            res = previewEffect(particle_json, texture_bytes, change_view=False, additional_data={"source": particle.as_posix()})
            if res[0]:
                loaded += 1
            else:
                print(f"Failed to preview ({particle}, {texture}) with error {res[1]}")
                
        else:
            print(f"No texture found for {particle}")
    return (True, f"Loaded {loaded} particles.")
    