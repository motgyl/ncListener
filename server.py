#!/usr/bin/env python3
"""
Message server for peer-to-peer communication via netcat
"""

import socket
import threading
import json
from datetime import datetime
import os
import base64

HOST = '0.0.0.0'
PORT = 7002
MESSAGES_FILE = 'messages.json'
FILES_DIR = 'shared_files'

# Create files directory if it doesn't exist
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

# Shared message storage: [messages]
messages = []
# Active users dictionary: {socket: username}
users = {}
lock = threading.Lock()


def load_messages():
    """Load messages from file"""
    global messages
    if os.path.exists(MESSAGES_FILE):
        try:
            with open(MESSAGES_FILE, 'r') as f:
                messages = json.load(f)
                print(f"[INFO] Loaded {len(messages)} messages from file")
        except Exception as e:
            print(f"[ERROR] Failed to load messages: {e}")
            messages = []
    else:
        messages = []


def save_messages():
    """Save messages to file"""
    try:
        with open(MESSAGES_FILE, 'w') as f:
            json.dump(messages, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save messages: {e}")


def format_help():
    """Returns command help"""
    return """
========================================
     Message Server (Memo)
========================================

Available commands:
  help              - show this help
  login <name>      - login with username
  post              - start posting (enter multiple lines, type 'END' on new line to finish)
  view              - view all messages
  upload            - upload a file (binary-safe)
  files             - list available files
  download <name>   - download a file by name
  users             - list all active users
  quit              - exit

Examples:
  login alice
  post
  [enter text...]
  END
  upload
  files
  download myfile.txt
  quit
""".strip()


def handle_client(client_socket, addr):
    """Client connection handler"""
    print(f"[CONNECT] {addr}")
    current_user = None
    
    try:
        # Send welcome message
        client_socket.send(b"Welcome to the message server!\n")
        client_socket.send(b"Type 'help' for commands\n\n")
        
        while True:
            data = client_socket.recv(1024).decode('utf-8').strip()
            
            if not data:
                break
            
            parts = data.split(maxsplit=1)
            command = parts[0].lower()
            
            # Command: help
            if command == 'help':
                client_socket.send(format_help().encode('utf-8') + b'\n')
            
            # Command: login
            elif command == 'login':
                if len(parts) < 2:
                    client_socket.send(b"Usage: login <name>\n")
                    continue
                
                new_user = parts[1]
                
                with lock:
                    if current_user:
                        del users[client_socket]
                    current_user = new_user
                    users[client_socket] = current_user
                
                msg = f"[OK] Logged in as '{current_user}'\n".encode('utf-8')
                client_socket.send(msg)
                print(f"[LOGIN] {current_user} ({addr})")
            
            # Command: send
            elif command == 'send' or command == 'post':
                if not current_user:
                    client_socket.send(b"[ERR] Please login first (login <name>)\n")
                    continue
                
                client_socket.send(b"Enter your message (type 'END' on new line to finish):\n")
                
                message_lines = []
                while True:
                    try:
                        line = client_socket.recv(1024).decode('utf-8').rstrip('\n\r')
                        if line == 'END':
                            break
                        message_lines.append(line)
                    except:
                        break
                
                if not message_lines:
                    client_socket.send(b"[ERR] Empty message\n")
                    continue
                
                full_message = '\n'.join(message_lines)
                
                with lock:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    msg_obj = {
                        'from': current_user,
                        'text': full_message,
                        'time': timestamp
                    }
                    messages.append(msg_obj)
                    save_messages()
                
                response = f"[OK] Message posted\n"
                client_socket.send(response.encode('utf-8'))
                print(f"[MESSAGE] {current_user} posted message")
            
            # Command: read
            elif command == 'read' or command == 'view':
                with lock:
                    all_messages = list(messages)
                
                if not all_messages:
                    client_socket.send(b"No messages yet\n")
                else:
                    response = f"\n{'='*60}\n"
                    response += f"All messages ({len(all_messages)} total):\n"
                    response += f"{'='*60}\n"
                    
                    for i, msg in enumerate(all_messages, 1):
                        response += f"\n[{i}] {msg['from']} ({msg['time']})\n"
                        response += f"    {msg['text']}\n"
                    
                    response += f"\n{'='*60}\n"
                    
                    client_socket.send(response.encode('utf-8'))
            
            # Command: files
            elif command == 'files':
                try:
                    files = os.listdir(FILES_DIR)
                    if not files:
                        client_socket.send(b"No files available\n")
                    else:
                        response = f"\nAvailable files ({len(files)} total):\n"
                        response += "="*60 + "\n"
                        for i, fname in enumerate(files, 1):
                            fpath = os.path.join(FILES_DIR, fname)
                            fsize = os.path.getsize(fpath)
                            response += f"[{i}] {fname} ({fsize} bytes)\n"
                        response += "="*60 + "\n"
                        client_socket.send(response.encode('utf-8'))
                except Exception as e:
                    client_socket.send(f"[ERR] {str(e)}\n".encode('utf-8'))
            
            # Command: upload
            elif command == 'upload':
                if not current_user:
                    client_socket.send(b"[ERR] Please login first (login <name>)\n")
                    continue
                
                client_socket.send(b"Enter filename: ")
                try:
                    filename = client_socket.recv(1024).decode('utf-8').strip()
                    if not filename or '/' in filename or '\\' in filename:
                        client_socket.send(b"[ERR] Invalid filename\n")
                        continue
                    
                    client_socket.send(b"Enter file size in bytes: ")
                    file_size = int(client_socket.recv(1024).decode('utf-8').strip())
                    
                    if file_size <= 0 or file_size > 100 * 1024 * 1024:  # Max 100MB
                        client_socket.send(b"[ERR] Invalid file size\n")
                        continue
                    
                    client_socket.send(b"Ready to receive file (sending in base64):\n")
                    
                    # Receive base64-encoded file
                    received_data = b''
                    bytes_remaining = file_size * 4 // 3 + 10  # Base64 is ~33% larger
                    
                    while len(received_data) < bytes_remaining:
                        chunk = client_socket.recv(8192)
                        if not chunk:
                            break
                        received_data += chunk
                    
                    # Decode from base64
                    try:
                        file_content = base64.b64decode(received_data.strip())
                    except Exception as e:
                        client_socket.send(f"[ERR] Decoding failed: {str(e)}\n".encode('utf-8'))
                        continue
                    
                    # Save file
                    filepath = os.path.join(FILES_DIR, filename)
                    with open(filepath, 'wb') as f:
                        f.write(file_content)
                    
                    response = f"[OK] File '{filename}' uploaded ({len(file_content)} bytes)\n"
                    client_socket.send(response.encode('utf-8'))
                    print(f"[UPLOAD] {current_user} uploaded {filename}")
                
                except ValueError:
                    client_socket.send(b"[ERR] Invalid input\n")
                except Exception as e:
                    client_socket.send(f"[ERR] {str(e)}\n".encode('utf-8'))
            
            # Command: download
            elif command == 'download':
                if len(parts) < 2:
                    client_socket.send(b"Usage: download <filename>\n")
                    continue
                
                filename = parts[1]
                if '/' in filename or '\\' in filename:
                    client_socket.send(b"[ERR] Invalid filename\n")
                    continue
                
                filepath = os.path.join(FILES_DIR, filename)
                
                if not os.path.exists(filepath):
                    client_socket.send(b"[ERR] File not found\n")
                    continue
                
                try:
                    with open(filepath, 'rb') as f:
                        file_content = f.read()
                    
                    # Encode to base64 for safe transmission
                    encoded = base64.b64encode(file_content)
                    
                    response = f"[OK] Downloading {filename} ({len(file_content)} bytes)\n".encode('utf-8')
                    response += encoded
                    response += b"\n"
                    
                    client_socket.send(response)
                    print(f"[DOWNLOAD] {current_user} downloaded {filename}")
                
                except Exception as e:
                    client_socket.send(f"[ERR] {str(e)}\n".encode('utf-8'))
            elif command == 'users':
                with lock:
                    users_list = list(set(users.values()))
                
                if not users_list:
                    client_socket.send(b"No active users\n")
                else:
                    response = "Active users:\n"
                    for user in sorted(users_list):
                        marker = " (you)" if user == current_user else ""
                        response += f"  * {user}{marker}\n"
                    client_socket.send(response.encode('utf-8'))
            
            # Command: quit
            elif command == 'quit' or command == 'exit':
                client_socket.send(b"Goodbye!\n")
                break
            
            else:
                client_socket.send(b"[ERR] Unknown command. Type 'help' for commands\n")
    
    except ConnectionResetError:
        print(f"[DISCONNECT] {addr}")
    except Exception as e:
        print(f"[ERROR] {addr}: {e}")
    finally:
        with lock:
            if client_socket in users:
                print(f"[LOGOUT] {users[client_socket]} ({addr})")
                del users[client_socket]
        client_socket.close()


def start_server():
    """Start the server"""
    load_messages()
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    
    print(f"[SERVER] Started on {HOST}:{PORT}")
    print(f"[INFO] Connect with: nc localhost {PORT}\n")
    
    try:
        while True:
            client_socket, addr = server.accept()
            # Run client handler in separate thread
            thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\n\n[INFO] Server stopped")
    finally:
        server.close()


if __name__ == '__main__':
    start_server()
