#!/usr/bin/env python3
"""
Advanced message server with chat, tasks, and AI integration
Features: authentication, chat, task management, Gemini AI with Key Rotation
"""

import socket
import threading
import json
from datetime import datetime
import os
import sys
import logging
import hashlib
import uuid
from typing import Dict, List, Optional, Tuple

# Google Gemini Imports
try:
    import google.generativeai as genai
    from google.api_core import exceptions
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai library not installed. AI features will be disabled.")
    print("Run: pip install google-generativeai")

HOST = '0.0.0.0'
PORT = 7002
DATA_DIR = 'data'
LOGS_DIR = 'logs'

# ==========================================
# CONFIGURATION: GEMINI KEYS & MODEL
# ==========================================
# Вставьте сюда ваш пак ключей. Если один переполнится, сервер переключится на следующий.
GEMINI_API_KEYS = [
    "AIzaSy",
    "AIzaSy...KEY_2",
    "AIzaSy...KEY_3"
]

# Используем быструю модель (Gemini 2.0 Flash Experimental - актуальный аналог "3 flash" на данный момент)
GEMINI_MODEL_NAME = "gemini-3-flash-preview"  # Проверьте актуальное имя модели в документации Google GenAI

# Create directories if they don't exist
for d in [DATA_DIR, LOGS_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# Setup logging
log_file = os.path.join(LOGS_DIR, 'server.log')
logger = logging.getLogger('server')
logger.setLevel(logging.DEBUG)

# File handler
fh = logging.FileHandler(log_file)
fh.setLevel(logging.DEBUG)

# Console handler
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

# Data storage
users_db: Dict[str, dict] = {}  # {username: {password_hash, created_at}}
sessions: Dict[str, str] = {}   # {session_id: username}
chat_messages: List[dict] = []
tasks: Dict[str, dict] = {}      # {task_id: {title, description, solution, status, created_by, created_at}}
ai_chat_history: Dict[str, List[dict]] = {}  # {username: [{role, content}]}

lock = threading.Lock()

# Data file paths
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
CHAT_FILE = os.path.join(DATA_DIR, 'chat.json')
TASKS_FILE = os.path.join(DATA_DIR, 'tasks.json')
AI_CHAT_FILE = os.path.join(DATA_DIR, 'ai_chat.json')


# ==========================================
# GEMINI MANAGER CLASS
# ==========================================
class GeminiManager:
    def __init__(self, api_keys, model_name):
        self.api_keys = api_keys
        self.model_name = model_name
        self.current_key_index = 0
        self.model = None
        
        if GEMINI_AVAILABLE and self.api_keys:
            self._initialize_client()

    def _initialize_client(self):
        """Initializes the client with the current key."""
        if not self.api_keys:
            return

        current_key = self.api_keys[self.current_key_index]
        try:
            genai.configure(api_key=current_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"[Gemini] Switched to API Key index: {self.current_key_index}")
        except Exception as e:
            logger.error(f"[Gemini] Init error: {e}")

    def _rotate_key(self):
        """Rotates to the next API key."""
        if not self.api_keys:
            return
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.warning(f"[Gemini] Quota exhausted. Rotating to key index {self.current_key_index}...")
        self._initialize_client()


    def generate_content(self, history_formatted, attempts=0):
        """
        Generates content with key rotation logic.
        history_formatted: List of messages in Gemini format [{'role': 'user', 'parts': ['...']}, ...]
        """
        if not GEMINI_AVAILABLE or not self.model:
            return "Error: Gemini not initialized or library missing."

        if attempts >= len(self.api_keys):
            logger.error("[Gemini] All keys exhausted.")
            return "Error: Server is currently overloaded (All API keys exhausted). Please try again later."

        try:
            # We use chat mode with history
            chat = self.model.start_chat(history=history_formatted[:-1]) # All but last
            last_msg = history_formatted[-1]['parts'][0]
            
            response = chat.send_message(last_msg)
            return response.text

        except exceptions.ResourceExhausted:
            self._rotate_key()
            return self.generate_content(history_formatted, attempts + 1)
        
        except Exception as e:
            logger.error(f"[Gemini] Generation error: {e}")
            return f"Error processing request: {str(e)}"

# Initialize the global manager
gemini_manager = GeminiManager(GEMINI_API_KEYS, GEMINI_MODEL_NAME)


def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def load_data():
    """Load all data from files"""
    global users_db, chat_messages, tasks, ai_chat_history
    
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                users_db = json.load(f)
        except:
            users_db = {}
    
    if os.path.exists(CHAT_FILE):
        try:
            with open(CHAT_FILE, 'r') as f:
                chat_messages = json.load(f)
        except:
            chat_messages = []
    
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, 'r') as f:
                tasks = json.load(f)
        except:
            tasks = {}
    
    if os.path.exists(AI_CHAT_FILE):
        try:
            with open(AI_CHAT_FILE, 'r') as f:
                ai_chat_history = json.load(f)
        except:
            ai_chat_history = {}


def save_data():
    """Save all data to files"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users_db, f, indent=2)
        with open(CHAT_FILE, 'w') as f:
            json.dump(chat_messages, f, indent=2)
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)
        with open(AI_CHAT_FILE, 'w') as f:
            json.dump(ai_chat_history, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save data: {e}")


def format_help():
    """Returns command help"""
    return """
========================================
      Messenger with Tasks & AI
========================================

AUTHENTICATION:
  register <username> <password>  - register new account
  login <username> <password>     - login to your account
  logout                          - logout

CHAT (after login):
  chat send <message>             - send message to chat
  chat view                       - view all messages
  chat view <count>               - view last N messages

TASKS (after login):
  task create <title>             - create new task
  task add-desc <task_id>         - add description (multiline, end with 'END')
  task add-sol <task_id>          - add solution (multiline, end with 'END')
  task list                       - list all tasks
  task view <task_id>             - view task details
  task status <task_id> <status>  - change status (pending/in_progress/solved)
  task delete <task_id>           - delete task

AI CHAT (after login):
  ai <message>                    - chat with AI (Gemini Flash)
  ai clear                        - clear AI chat history

OTHER:
  help                            - show this help
  quit                            - exit
""".strip()


def generate_session_id():
    """Generate a new session ID"""
    return str(uuid.uuid4())


def authenticate_user(username: str, password: str) -> Optional[str]:
    """Authenticate user and return session ID"""
    with lock:
        if username not in users_db:
            return None
        
        if users_db[username]['password'] != hash_password(password):
            return None
        
        session_id = generate_session_id()
        sessions[session_id] = username
        return session_id


def register_user(username: str, password: str) -> bool:
    """Register new user"""
    with lock:
        if username in users_db:
            return False
        
        if len(username) < 3 or len(password) < 4:
            return False
        
        users_db[username] = {
            'password': hash_password(password),
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_data()
        return True


def get_ai_response(user_message: str, user_history: List[dict]) -> str:
    """
    Get response from Gemini API via GeminiManager.
    Converts internal history format to Gemini format.
    Internal: [{'role': 'user', 'content': '...'}, {'role': 'assistant', 'content': '...'}]
    Gemini:   [{'role': 'user', 'parts': ['...']}, {'role': 'model', 'parts': ['...']}]
    """
    if not GEMINI_AVAILABLE:
        return "[ERROR] google-generativeai library is not installed."
    
    # Convert history to Gemini format
    gemini_history = []
    
    # Add previous context (limit to last 10 turns to save context window/tokens)
    for msg in user_history[-20:]: 
        role = 'user' if msg['role'] == 'user' else 'model'
        content = msg['content']
        gemini_history.append({
            "role": role,
            "parts": [content]
        })
    
    # Ensure the last message in history is the current one we want to send
    # (The caller of this function appends the user message to history before calling)
    
    return gemini_manager.generate_content(gemini_history)


def handle_client(client_socket, addr):
    """Handle client connection"""
    logger.info(f"Client connected: {addr}")
    current_user = None
    session_id = None
    
    try:
        client_socket.send(b"Welcome! Type 'help' for commands\n\n")
        
        while True:
            data = client_socket.recv(1024).decode('utf-8').strip()
            
            if not data:
                break
            
            parts = data.split(maxsplit=1)
            command = parts[0].lower()
            
            # Authentication commands (no login required)
            if command == 'help':
                client_socket.send(format_help().encode('utf-8') + b'\n')
            
            elif command == 'register':
                if current_user:
                    client_socket.send(b"[ERR] Already logged in\n")
                    continue
                
                if len(parts) < 2:
                    client_socket.send(b"Usage: register <username> <password>\n")
                    continue
                
                try:
                    reg_parts = parts[1].split()
                    if len(reg_parts) < 2:
                        client_socket.send(b"Usage: register <username> <password>\n")
                        continue
                    
                    username, password = reg_parts[0], reg_parts[1]
                    if register_user(username, password):
                        client_socket.send(f"[OK] User '{username}' registered\n".encode('utf-8'))
                        logger.info(f"New user registered: {username}")
                    else:
                        client_socket.send(b"[ERR] Username taken or invalid\n")
                except:
                    client_socket.send(b"[ERR] Invalid format\n")
            
            elif command == 'login':
                if current_user:
                    client_socket.send(b"[ERR] Already logged in\n")
                    continue
                
                if len(parts) < 2:
                    client_socket.send(b"Usage: login <username> <password>\n")
                    continue
                
                try:
                    login_parts = parts[1].split()
                    if len(login_parts) < 2:
                        client_socket.send(b"Usage: login <username> <password>\n")
                        continue
                    
                    username, password = login_parts[0], login_parts[1]
                    session_id = authenticate_user(username, password)
                    
                    if session_id:
                        current_user = username
                        client_socket.send(f"[OK] Logged in as '{username}'\n".encode('utf-8'))
                        logger.info(f"User '{username}' logged in from {addr}")
                    else:
                        client_socket.send(b"[ERR] Invalid credentials\n")
                except:
                    client_socket.send(b"[ERR] Invalid format\n")
            
            # Commands requiring login
            elif not current_user:
                client_socket.send(b"[ERR] Please login first\n")
            
            elif command == 'logout':
                if session_id:
                    with lock:
                        if session_id in sessions:
                            del sessions[session_id]
                current_user = None
                session_id = None
                client_socket.send(b"[OK] Logged out\n")
            
            # CHAT commands
            elif command == 'chat':
                if len(parts) < 2:
                    client_socket.send(b"Usage: chat send <message> | chat view [count]\n")
                    continue
                
                action_parts = parts[1].split(maxsplit=1)
                action = action_parts[0].lower()
                
                if action == 'send':
                    if len(action_parts) < 2:
                        client_socket.send(b"[ERR] Empty message\n")
                        continue

                    
                    message_text = action_parts[1]
                    
                    with lock:
                        msg_obj = {
                            'from': current_user,
                            'text': message_text,
                            'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        chat_messages.append(msg_obj)
                        save_data()
                    
                    client_socket.send(b"[OK] Message sent\n")
                    logger.info(f"User '{current_user}' sent chat message")
                
                elif action == 'view':
                    count = 100
                    if len(action_parts) > 1:
                        try:
                            count = int(action_parts[1])
                        except:
                            pass
                    
                    with lock:
                        msgs = list(chat_messages[-count:])
                    
                    if not msgs:
                        client_socket.send(b"No messages yet\n")
                    else:
                        response = f"\n{'='*60}\nChat ({len(msgs)} messages):\n{'='*60}\n"
                        for i, msg in enumerate(msgs, 1):
                            response += f"[{i}] {msg['from']} ({msg['time']})\n    {msg['text']}\n"
                        response += f"{'='*60}\n"
                        client_socket.send(response.encode('utf-8'))
                else:
                    client_socket.send(b"[ERR] Unknown chat action\n")
            
            # TASK commands
            elif command == 'task':
                if len(parts) < 2:
                    client_socket.send(b"Usage: task create <title> | task view <id> | task list | task status <id> <status>\n")
                    continue
                
                action_parts = parts[1].split(maxsplit=1)
                action = action_parts[0].lower()
                
                if action == 'create':
                    if len(action_parts) < 2:
                        client_socket.send(b"[ERR] Title required\n")
                        continue
                    
                    title = action_parts[1]
                    task_id = str(uuid.uuid4())[:8]
                    
                    with lock:
                        tasks[task_id] = {
                            'title': title,
                            'description': '',
                            'solution': '',
                            'status': 'pending',
                            'created_by': current_user,
                            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        save_data()
                    
                    client_socket.send(f"[OK] Task created: {task_id}\n".encode('utf-8'))
                    logger.info(f"User '{current_user}' created task {task_id}")
                
                elif action == 'list':
                    with lock:
                        task_list = list(tasks.items())
                    
                    if not task_list:
                        client_socket.send(b"No tasks yet\n")
                    else:
                        response = f"\n{'='*60}\nTasks ({len(task_list)} total):\n{'='*60}\n"
                        for task_id, task in task_list:
                            response += f"[{task_id}] {task['title']} ({task['status']})\n"
                            response += f"         by {task['created_by']} - {task['created_at']}\n"
                        response += f"{'='*60}\n"
                        client_socket.send(response.encode('utf-8'))
                
                elif action == 'view':
                    try:
                        view_parts = action_parts[1].split()
                        task_id = view_parts[0]
                    except:
                        client_socket.send(b"Usage: task view <task_id>\n")
                        continue

                    
                    with lock:
                        task = tasks.get(task_id)
                    
                    if not task:
                        client_socket.send(b"[ERR] Task not found\n")
                    else:
                        response = f"\n{'='*60}\nTask: {task_id}\n{'='*60}\n"
                        response += f"Title:       {task['title']}\n"
                        response += f"Status:      {task['status']}\n"
                        response += f"Created by:  {task['created_by']}\n"
                        response += f"Created at:  {task['created_at']}\n"
                        response += f"\nDescription:\n{task['description'] or '(none)'}\n"
                        response += f"\nSolution:\n{task['solution'] or '(none)'}\n"
                        response += f"{'='*60}\n"
                        client_socket.send(response.encode('utf-8'))
                
                elif action == 'add-desc':
                    try:
                        desc_parts = action_parts[1].split()
                        task_id = desc_parts[0]
                    except:
                        client_socket.send(b"Usage: task add-desc <task_id>\n")
                        continue
                    
                    with lock:
                        if task_id not in tasks:
                            client_socket.send(b"[ERR] Task not found\n")
                            continue
                    
                    client_socket.send(b"Enter description (type 'END' on new line to finish):\n")
                    
                    desc_lines = []
                    while True:
                        try:
                            line = client_socket.recv(1024).decode('utf-8').rstrip('\n\r')
                            if line == 'END':
                                break
                            desc_lines.append(line)
                        except:
                            break
                    
                    description = '\n'.join(desc_lines)
                    
                    with lock:
                        if task_id in tasks:
                            tasks[task_id]['description'] = description
                            save_data()
                    
                    client_socket.send(b"[OK] Description saved\n")
                
                elif action == 'add-sol':
                    try:
                        sol_parts = action_parts[1].split()
                        task_id = sol_parts[0]
                    except:
                        client_socket.send(b"Usage: task add-sol <task_id>\n")
                        continue
                    
                    with lock:
                        if task_id not in tasks:
                            client_socket.send(b"[ERR] Task not found\n")
                            continue
                    
                    client_socket.send(b"Enter solution (type 'END' on new line to finish):\n")
                    
                    sol_lines = []
                    while True:
                        try:
                            line = client_socket.recv(1024).decode('utf-8').rstrip('\n\r')
                            if line == 'END':
                                break
                            sol_lines.append(line)
                        except:
                            break
                    
                    solution = '\n'.join(sol_lines)
                    
                    with lock:
                        if task_id in tasks:
                            tasks[task_id]['solution'] = solution
                            save_data()
                    
                    client_socket.send(b"[OK] Solution saved\n")
                
                elif action == 'status':
                    try:
                        status_parts = action_parts[1].split()
                        task_id = status_parts[0]
                        new_status = status_parts[1] if len(status_parts) > 1 else None

                    except:
                        client_socket.send(b"Usage: task status <task_id> <status>\n")
                        continue
                    
                    if new_status not in ['pending', 'in_progress', 'solved']:
                        client_socket.send(b"[ERR] Status must be: pending, in_progress, or solved\n")
                        continue
                    
                    with lock:
                        if task_id not in tasks:
                            client_socket.send(b"[ERR] Task not found\n")
                        else:
                            tasks[task_id]['status'] = new_status
                            save_data()
                            client_socket.send(f"[OK] Status changed to '{new_status}'\n".encode('utf-8'))
                
                elif action == 'delete':
                    try:
                        del_parts = action_parts[1].split()
                        task_id = del_parts[0]
                    except:
                        client_socket.send(b"Usage: task delete <task_id>\n")
                        continue
                    
                    with lock:
                        if task_id in tasks:
                            del tasks[task_id]
                            save_data()
                            client_socket.send(b"[OK] Task deleted\n")
                        else:
                            client_socket.send(b"[ERR] Task not found\n")
                else:
                    client_socket.send(b"[ERR] Unknown task action\n")
            
            # AI CHAT commands
            elif command == 'ai':
                if len(parts) < 2:
                    client_socket.send(b"Usage: ai <message> | ai clear\n")
                    continue
                
                ai_input = parts[1].lower()
                
                if ai_input == 'clear':
                    with lock:
                        if current_user in ai_chat_history:
                            ai_chat_history[current_user] = []
                            save_data()
                    client_socket.send(b"[OK] AI chat history cleared\n")
                else:
                    message = parts[1]
                    
                    with lock:
                        if current_user not in ai_chat_history:
                            ai_chat_history[current_user] = []
                        
                        ai_chat_history[current_user].append({
                            'role': 'user',
                            'content': message
                        })
                        user_history = list(ai_chat_history[current_user])
                    
                    # Get response from Gemini via Manager
                    response_text = get_ai_response(message, user_history)
                    
                    with lock:
                        if current_user in ai_chat_history:
                            ai_chat_history[current_user].append({
                                'role': 'assistant',
                                'content': response_text
                            })
                            save_data()
                    
                    client_socket.send(f"AI: {response_text}\n".encode('utf-8'))
                    logger.info(f"User '{current_user}' sent AI message")
            
            elif command == 'quit' or command == 'exit':
                client_socket.send(b"Goodbye!\n")
                break
            
            else:
                client_socket.send(b"[ERR] Unknown command. Type 'help' for commands\n")
    
    except ConnectionResetError:
        logger.warning(f"Connection reset by peer: {addr}")
    except Exception as e:
        logger.error(f"Error handling client {addr}: {e}")
    finally:
        if session_id and session_id in sessions:
            with lock:
                del sessions[session_id]
        client_socket.close()


def start_server():
    """Start the server"""
    load_data()
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    
    logger.info(f"Server started on {HOST}:{PORT}")
    logger.info(f"Clients can connect with: nc {HOST} {PORT}")
    
    try:
        while True:
            client_socket, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        server.close()


if __name__ == '__main__':
    start_server()
