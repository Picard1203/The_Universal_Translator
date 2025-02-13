# client/client.py
import socket
import ssl
import threading
import logging
import time
import requests

# --- Configuration (update as needed) ---
SERVER_HOST = '127.0.0.1'      # Use your server's IP or hostname
SERVER_PORT = 5001
SERVER_CERT = 'server/cert.pem'  # Path to the server's certificate
FLASK_API_URL = 'http://127.0.0.1:5002'  # Flask API endpoint
# -------------------------------------------

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Prompt user for their language code
client_language = input("Enter your language code (e.g., 'en' or 'he'): ").strip().lower()
if not client_language:
    client_language = 'en'

# Client ID is either entered by the user or auto-generated.
CLIENT_ID = None

def update_sync_via_api(client_id, phase):
    """Update this client’s phase via the Flask API."""
    url = f"{FLASK_API_URL}/update_sync"
    data = {'client_id': client_id, 'phase': phase}
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            logging.debug(f"[Client {client_id}] Sync update result: {result}")
            return result.get('all_ready', False)
        else:
            logging.error(f"[Client {client_id}] Failed to update sync: {response.text}")
    except Exception as e:
        logging.error(f"[Client {client_id}] Exception during sync update: {e}")
    return False

def listen_for_messages(tls_sock):
    """Listen for broadcast messages from the server."""
    while True:
        try:
            data = tls_sock.recv(4096)
            if not data:
                logging.info("[Client] Server closed connection.")
                break
            message = data.decode()
            if message.startswith("MSG|"):
                final_text = message.split("|", 1)[1]
                logging.info(f"[Client] Final message received: {final_text}")
                # Upon receiving the broadcast, update the sync state via the API
                update_sync_via_api(CLIENT_ID, 2)  # Phase RECEIVED
                update_sync_via_api(CLIENT_ID, 6)  # Phase READY
        except Exception as e:
            logging.error(f"[Client] Error receiving message: {e}")
            break

def main():
    global CLIENT_ID
    # Create a socket and wrap it with TLS.
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=SERVER_CERT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tls_sock = context.wrap_socket(sock, server_hostname=SERVER_HOST)

    try:
        tls_sock.connect((SERVER_HOST, SERVER_PORT))
        logging.info("[Client] Connected securely to server.")
        CLIENT_ID = input("Enter your client identifier (or leave blank to auto-generate): ").strip()
        if not CLIENT_ID:
            CLIENT_ID = str(int(time.time() * 1000) % 100000)
        logging.info(f"[Client] Using CLIENT_ID: {CLIENT_ID}")

        # Start a listener thread to receive messages from the server.
        listener_thread = threading.Thread(target=listen_for_messages, args=(tls_sock,), daemon=True)
        listener_thread.start()

        # Prompt the user for a message to send.
        user_message = input("Enter your message: ")
        full_message = f"{client_language}|{user_message}"
        tls_sock.sendall(full_message.encode())
        logging.info("[Client] Message sent to server.")
        # Update sync: Phase SENT.
        update_sync_via_api(CLIENT_ID, 1)

        # Continue running to receive messages.
        while True:
            time.sleep(1)
    except Exception as e:
        logging.error(f"[Client] Error: {e}")
    finally:
        tls_sock.close()
        logging.info("[Client] Connection closed.")

if __name__ == '__main__':
    main()
