import argparse
import json
import sys
from .interface import previewEffect, setTimeout, setView, queryPID, stopServer, startServer, checkStatus, removeEffect, clearEffects, galleryFromFolder

def main():
    parser = argparse.ArgumentParser(description="Command line interface for preview server.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # preview
    preview_parser = subparsers.add_parser("preview", help="Send one or more preview commands.")
    preview_parser.add_argument("--particle", action="append", help="Path to particle JSON file")
    preview_parser.add_argument("--texture", action="append", help="Path to texture PNG file")

    # setView
    setview_parser = subparsers.add_parser("setView", help="Set the current view.")
    setview_parser.add_argument("identifier", type=str, help="View identifier")
    
    # removeEffect
    removeeffect_parser = subparsers.add_parser("removeEffect", help="Remove one or more effects.")
    removeeffect_parser.add_argument("--identifier", action="append", help="effect identifier")

    # clearEffects
    subparsers.add_parser("clearEffects", help="Remove all effects.")

    # setTimeout
    settimeout_parser = subparsers.add_parser("setTimeout", help="Set the preview timeout.")
    settimeout_parser.add_argument("timeout", type=float, help="Timeout in seconds")

    # queryPID
    subparsers.add_parser("queryPID", help="Query the server PID.")

    # startServer
    startserver_parser = subparsers.add_parser("startServer", help="Start the preview server.")
    startserver_parser.add_argument("--timeout", type=float, default=None, help="Optional server timeout in seconds")

    # stopServer
    subparsers.add_parser("stopServer", help="Stop the preview server.")

    # checkStatus
    subparsers.add_parser("checkStatus", help="Check the preview server status.")
    
    # loadGallery
    loadgallery_parser = subparsers.add_parser("loadGallery", help="Load gallery from particles in folder(s).")
    loadgallery_parser.add_argument("--folder", action="append", help="Folder path")

    args = parser.parse_args()

    if args.command == "preview":
        particles = args.particle or []
        textures = args.texture or []

        if len(particles) != len(textures):
            print("Error: Must provide an equal number of --particle and --texture arguments.", file=sys.stderr)
            sys.exit(1)

        for p_path, t_path in zip(particles, textures):
            try:
                with open(p_path, 'r', encoding='utf-8') as f:
                    particle_dict = json.load(f)
                with open(t_path, 'rb') as f:
                    texture_bytes = f.read()
                print(previewEffect(particle_dict, texture_bytes)[1])
            except Exception as e:
                print(f"Error processing {p_path} or {t_path}: {e}", file=sys.stderr)
                sys.exit(1)
        print(f"Sent {len(particles)} particles to server.")

    elif args.command == "setView":
        print(setView(args.identifier)[1])

    elif args.command == "setTimeout":
        print(setTimeout(args.timeout)[1])

    elif args.command == "queryPID":
        print(queryPID()[1])

    elif args.command == "startServer":
        print(startServer(timeout=args.timeout)[1])

    elif args.command == "stopServer":
        print(stopServer()[1])

    elif args.command == "checkStatus":
        url = checkStatus()
        if url:
            print(f"Server is up at {url}")
        else:
            print("Server is down.")
            
    elif args.command == "removeEffect":
        particles = args.identifier or []
        for particle in particles:
            print(removeEffect(particle)[1])
            
    elif args.command == "clearEffects":
        print(clearEffects()[1])
        
    elif args.command == "loadGallery":
        folders: list[str] = args.folder or []
        for folder in folders:
            print(galleryFromFolder(folder)[1])

if __name__ == "__main__":  
    main()