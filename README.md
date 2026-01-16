# Message Server (Memo Server)

Simple TCP server for sharing messages and files with all connected users via `netcat`. Messages and files are persisted and available to users who connect later.

## Installation

No additional dependencies required. Python 3.6+

## Running the server

```bash
python3 server.py
```

The server will run on `localhost:5555`. 
- Messages are saved in `messages.json` and automatically loaded on startup
- Files are stored in `shared_files/` directory

## Connecting a client

In a separate terminal, connect using `netcat`:

```bash
nc localhost 5555
```

## Commands

| Command | Description |
|---------|---------|
| `help` | Show help |
| `login <name>` | Login with username |
| `post` | Start posting multi-line message (type 'END' on new line to finish) |
| `view` | View all messages |
| `upload` | Upload a file (binary-safe, base64 encoded) |
| `files` | List available files |
| `download <name>` | Download a file by name |
| `users` | Show list of active users |
| `quit` | Disconnect from server |

## Usage example

**Window 1 (Server):**
```bash
$ python3 server.py
[SERVER] Started on 0.0.0.0:5555
[INFO] Connect with: nc localhost 5555
[INFO] Loaded 0 messages from file
```

**Window 2 (User Alice):**
```bash
$ nc localhost 5555
Welcome to the message server!
Type 'help' for commands

login alice
[OK] Logged in as 'alice'
post
Enter your message (type 'END' on new line to finish):
Hello everyone!
This is a multi-line message.
I can write as much as I want!
END
[OK] Message posted
```

**Window 3 (User Bob, connects later):**
```bash
$ nc localhost 5555
Welcome to the message server!
Type 'help' for commands

login bob
[OK] Logged in as 'bob'
view
============================================================
All messages (1 total):
============================================================

[1] alice (2026-01-16 14:23:45)
    Hello everyone!
    This is a multi-line message.
    I can write as much as I want!

============================================================
post
Enter your message (type 'END' on new line to finish):
Hi Alice!
Great to see you!
END
[OK] Message posted
```

**Alice sees Bob's message:**
```bash
view
============================================================
All messages (2 total):
============================================================

[1] alice (2026-01-16 14:23:45)
    Hello everyone!
    This is a multi-line message.
    I can write as much as I want!

[2] bob (2026-01-16 14:24:10)
    Hi Alice!
    Great to see you!

============================================================
```

## Features

- Multiple simultaneous user connections
- All messages visible to all users
- Multi-line message support
- **File sharing**: upload and download files (binary-safe)
- Files persisted in `shared_files/` directory
- Messages persisted to `messages.json`
- Messages and files loaded on server startup
- Thread-safe operations
- Server-side event logging
- Simple text interface

## File Transfer

Files are transmitted using base64 encoding to ensure compatibility with text-based netcat connections. Maximum file size: 100MB.

### Using netcat (manual)

```bash
# Login and upload
login alice
upload
Enter filename: document.pdf
Enter file size in bytes: 12345
Ready to receive file (sending in base64):
[paste base64-encoded file content]
[OK] File 'document.pdf' uploaded

# Download
download document.pdf
[OK] Downloading document.pdf (12345 bytes)
[base64-encoded content...]
```

### Using client.py (automated)

```bash
# Upload a file
python3 client.py upload localhost:5555 document.pdf

# Download a file
python3 client.py download localhost:5555 document.pdf
python3 client.py download localhost:5555 document.pdf output.pdf  # Save as different name
```

## How it works

1. Server listens on port 5555
2. On startup, loads messages from `messages.json`
3. Each client is handled in a separate thread
4. User logs in with `login <name>`
5. Posted messages are stored on the server and saved to file
6. Using `view` command, all users can see all messages (including those posted before they connected)

## Data storage

Messages are stored in `messages.json` with the following format:

```json
[
  {
    "from": "alice",
    "text": "Hello everyone!\nThis is multi-line",
    "time": "2026-01-16 14:23:45"
  },
  {
    "from": "bob",
    "text": "Hi Alice!",
    "time": "2026-01-16 14:24:10"
  }
]
```

## Notes

- Messages persist across server restarts
- Files persist in `shared_files/` directory across server restarts  
- Multi-line messages are supported (use 'END' to finish)
- Files are transferred using base64 encoding (compatible with netcat)
- Maximum file size: 100MB
- For large-scale deployments, consider using a real database



