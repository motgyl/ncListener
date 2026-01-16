#!/usr/bin/env python3
"""
Simple client for file sharing server with command line interface
"""

import socket
import sys
import base64
import os

def send_command(sock, command):
    """Send command and receive response"""
    sock.send(command.encode('utf-8') + b'\n')
    return sock.recv(8192).decode('utf-8', errors='ignore')

def upload_file(sock, filepath):
    """Upload a file to server"""
    if not os.path.exists(filepath):
        print(f"[ERR] File not found: {filepath}")
        return
    
    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)
    
    print(f"[*] Uploading {filename} ({file_size} bytes)...")
    
    # Start upload command
    sock.send(b'upload\n')
    sock.recv(1024)  # "Enter filename"
    
    # Send filename
    sock.send(filename.encode('utf-8') + b'\n')
    sock.recv(1024)  # "Enter file size"
    
    # Send file size
    sock.send(str(file_size).encode('utf-8') + b'\n')
    sock.recv(1024)  # "Ready to receive"
    
    # Read and encode file
    with open(filepath, 'rb') as f:
        file_content = f.read()
    
    encoded = base64.b64encode(file_content)
    
    # Send encoded file
    sock.send(encoded + b'\n')
    
    # Get response
    response = sock.recv(1024).decode('utf-8')
    print(response.strip())

def download_file(sock, filename, output_path=None):
    """Download a file from server"""
    if output_path is None:
        output_path = filename
    
    print(f"[*] Downloading {filename}...")
    
    # Send download command
    sock.send(f'download {filename}\n'.encode('utf-8'))
    
    # Receive response
    response = sock.recv(1024).decode('utf-8', errors='ignore')
    print(response)
    
    if '[OK]' not in response:
        return
    
    # Receive base64-encoded file
    # Need to receive multiple chunks
    received = b''
    while True:
        chunk = sock.recv(8192)
        if not chunk:
            break
        received += chunk
        if b'\n' in chunk[-10:]:  # Last chunk likely contains newline
            break
    
    # Extract base64 content (skip the OK message)
    lines = received.split(b'\n')
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith(b'['):
            try:
                file_content = base64.b64decode(line)
                with open(output_path, 'wb') as f:
                    f.write(file_content)
                print(f"[OK] Saved to {output_path} ({len(file_content)} bytes)")
                return
            except:
                pass

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 client.py upload <host:port> <filepath>")
        print("  python3 client.py download <host:port> <filename> [output]")
        print("\nExample:")
        print("  python3 client.py upload localhost:5555 myfile.txt")
        print("  python3 client.py download localhost:5555 myfile.txt")
        sys.exit(1)
    
    action = sys.argv[1]
    
    try:
        host_port = sys.argv[2].split(':')
        host = host_port[0]
        port = int(host_port[1])
    except:
        print("[ERR] Invalid host:port format")
        sys.exit(1)
    
    # Connect to server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except:
        print(f"[ERR] Cannot connect to {host}:{port}")
        sys.exit(1)
    
    # Skip welcome messages
    sock.recv(1024)
    sock.recv(1024)
    
    # Ask for login
    print(sock.recv(1024).decode('utf-8', errors='ignore').strip())
    username = input("Username: ")
    sock.send(f'login {username}\n'.encode('utf-8'))
    print(sock.recv(1024).decode('utf-8').strip())
    
    if action == 'upload':
        if len(sys.argv) < 4:
            print("[ERR] Missing filepath")
            sys.exit(1)
        filepath = sys.argv[3]
        upload_file(sock, filepath)
    
    elif action == 'download':
        if len(sys.argv) < 4:
            print("[ERR] Missing filename")
            sys.exit(1)
        filename = sys.argv[3]
        output = sys.argv[4] if len(sys.argv) > 4 else filename
        download_file(sock, filename, output)
    
    else:
        print(f"[ERR] Unknown action: {action}")
        sys.exit(1)
    
    sock.close()

if __name__ == '__main__':
    main()
