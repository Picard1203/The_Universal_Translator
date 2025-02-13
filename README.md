```markdown
# Universal Translator

A real-time, multilingual chat system that:
- Connects clients securely with TLS
- Synchronizes message stages (using a server-side sync manager)
- Dynamically translates messages (using a placeholder or PyTorch model)
- Handles clients joining and leaving mid-transmission

---

## Directory Structure

```
universal_translator/
├── client/
│   ├── client.py         # Client application (prompts for language & ID, sends messages via TLS)
│   └── sync.py           # (Optional) Client-side vector clock & barrier classes
├── server/
│   ├── server.py         # Main TCP/TLS server for handling connections, messages, & translation
│   ├── flask_app.py      # Flask API for synchronization updates & status checks
│   └── sync_manager.py   # Server-side sync manager (tracks phases, barrier logic)
├── translation/
│   └── transformer.py    # Translation stub (reverse text; replace with your PyTorch model)
├── requirements.txt      # List of required Python packages
└── README.md             # This documentation
```

---

## Introduction

The **Universal Translator** aims to allow multiple clients, each with a preferred language, to chat in real time. Every message is synchronized so that all clients receive and display the final text simultaneously. Additionally, messages can be translated automatically if the sending and receiving languages differ.

**Key Features**:
- **TLS security**: End-to-end encrypted communication with an automatically generated self-signed certificate.
- **Synchronization**: Server-side phases for receiving, translating, and broadcasting messages, ensuring all participants remain in sync.
- **Translation**: A placeholder "reverse text" function that you can replace with a PyTorch model for real translations.

---

## Installation & Setup

1. **Clone or Download** the repository containing the `universal_translator/` folder.
2. **Create and activate a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate         # On Windows: .\venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Automatic TLS Certificate Generation

The server will automatically generate TLS certificates if they do not exist. The first time the server runs, it will create:
- `server/cert.pem` (self-signed certificate)
- `server/key.pem` (private key)

If you prefer to generate your own certificate, delete these files and use the following command:
   ```bash
   openssl req -x509 -newkey rsa:4096 -keyout server/key.pem -out server/cert.pem -days 365 -nodes
   ```

---

## Usage

### 1. Start the Server

1. Open a terminal, **enter** the `server/` directory, and run:
   ```bash
   python server.py
   ```
2. When prompted, **enter the target language** for the server (e.g., `en` for English).

The server now listens on a secure socket (`0.0.0.0:5001` by default) for incoming TLS connections.  

### 2. Start the Flask API (Optional but Recommended)

Open a **separate** terminal in the `server/` directory and run:
```bash
python flask_app.py
```
This launches the Flask server on `http://127.0.0.1:5002`, handling:
- `/update_sync`: Client updates of phases
- `/get_sync_status`: Querying synchronization status

### 3. Run One or More Clients

1. Open another terminal, **enter** the `client/` directory, and run:
   ```bash
   python client.py
   ```
2. The client will ask:
   - **Language code** (e.g., `he` for Hebrew or `en` for English)
   - **Client identifier** (optional; leave blank to auto-generate)
   - Then it will prompt you to **enter a message**.

When you send a message, it is transmitted securely to the server in the form `"LANG|MESSAGE"`.  
If the message language differs from the server’s target language, the stub translator in `transformer.py` will “reverse” the text (as a placeholder). You can run multiple clients in separate terminals to simulate a real group chat.

---

## Configuration

- **Port Configuration**:  
  Adjust `SERVER_PORT` in `server.py` or the Flask port in `flask_app.py` to suit your environment.
- **PyTorch Model Integration**:  
  Replace the stub code in `translation/transformer.py` with your actual PyTorch Transformer to perform real translation.

---

## How It Works

1. **TCP/TLS Connection**:  
   Each client connects to the server over a TLS-wrapped socket.  
2. **Phase Tracking (SyncManager)**:  
   - Clients are initially in `PHASE_WAITING` (0).  
   - After sending a message, the client’s phase is updated to `PHASE_SENT` (1).  
   - The server updates phases through `PHASE_RECEIVED`, `PHASE_CHECKED`, `PHASE_STARTED_TRANSLATION`, `PHASE_ENDED_TRANSLATION`, and finally `PHASE_READY`.  
   - Only when **all** active clients for that message reach `PHASE_READY` does the server broadcast.  
   - Once broadcast finishes, these clients are reset to `PHASE_WAITING`.  
3. **Translation Stub**:  
   If the client’s language matches the server’s target language, no translation occurs. Otherwise, the text is reversed (placeholder).  

---

## Further Improvements

- **Persistent Data**: Save messages to a database or file, so reconnecting clients can retrieve missed content.
- **Real Translation**: Replace the reversing function with a PyTorch model in `translation/transformer.py`.
- **Voice/Multimedia**: Extend to audio or video streams with real-time translation.
- **Authentication**: Implement user login and authentication via TLS certificates or tokens.
- **Scalability**: Use asynchronous networking (`asyncio` or `gevent`) or a message broker (e.g., RabbitMQ).

---

## Troubleshooting

- **TLS Errors**:  
  Ensure that the client trusts the server’s `cert.pem`. If using a self-signed certificate, the client will use the same `cert.pem` to verify the server.
- **Firewall**:  
  If hosting on a remote server, confirm the relevant ports (5001 for server, 5002 for Flask) are open.
- **Incorrect Format**:  
  The server expects `LANG|MESSAGE`. If the message is incorrectly formatted, an error will appear in logs.

---

## License

You can include license information (e.g., MIT license) if required by your institution or for open-source distribution.

---

**Happy coding!**
```
