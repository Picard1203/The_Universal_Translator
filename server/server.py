# server.py

import os
import subprocess
import socket
import ssl
import threading
import logging
import time

from translation.transformer import translate_text
from sync_manager import (
    sync_manager,
    PHASE_WAITING,
    PHASE_SENT,
    PHASE_RECEIVED,
    PHASE_CHECKED,
    PHASE_STARTED_TRANSLATION,
    PHASE_ENDED_TRANSLATION,
    PHASE_READY
)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# TLS certificate and key files to use or create
CERT_FILE = 'server/cert.pem'
KEY_FILE = 'server/key.pem'

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5001

# Global dictionary for active clients: {client_id: tls_socket}
clients = {}
client_lock = threading.Lock()
client_id_counter = 0

def generate_self_signed_cert_if_needed():
    """
    Checks if CERT_FILE and KEY_FILE exist. If not, uses OpenSSL to create them.
    """
    cert_exists = os.path.isfile(CERT_FILE)
    key_exists = os.path.isfile(KEY_FILE)
    if not cert_exists or not key_exists:
        logging.info("[Server] Generating self-signed certificate (cert.pem) and key (key.pem)...")
        try:
            # Adjust the '-subj' argument to set your preferred details (CN, O, etc.)
            subprocess.run([
                'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
                '-keyout', KEY_FILE,
                '-out', CERT_FILE,
                '-days', '365',
                '-nodes',
                '-subj', '/CN=localhost'
            ], check=True)
            logging.info("[Server] Successfully created self-signed TLS certificate and key.")
        except FileNotFoundError:
            logging.error(
                "[Server] Could not find OpenSSL on your system. "
                "Please install OpenSSL or create cert/key files manually."
            )
        except subprocess.CalledProcessError as e:
            logging.error(f"[Server] Error creating TLS certificate: {e}")
    else:
        logging.debug("[Server] Found existing TLS certificate and key; using them.")

def broadcast_message(message, exclude_client_id=None):
    with client_lock:
        for cid, client_sock in list(clients.items()):
            if cid != exclude_client_id:
                try:
                    client_sock.sendall(message.encode())
                except Exception as e:
                    logging.error(f"[Server] Error sending message to client {cid}: {e}")

def handle_client(conn, addr, client_id, target_language):
    logging.info(f"[Server] Client {client_id} connected from {addr}")
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                logging.info(f"[Server] Client {client_id} disconnected (no data).")
                break

            message = data.decode()
            logging.debug(f"[Server] Received from client {client_id}: {message}")
            try:
                # Expect message format: LANG|MESSAGE
                client_lang, text = message.split("|", 1)
                client_lang = client_lang.strip().lower()
            except ValueError:
                logging.error(f"[Server] Client {client_id} sent improperly formatted message.")
                continue

            # Snapshot of active clients for barrier logic
            with client_lock:
                active_client_ids = list(clients.keys())
            logging.debug(f"[Server] Active clients for barrier: {active_client_ids}")

            # Update phase: message received
            sync_manager.update_client_phase(client_id, PHASE_RECEIVED)

            # Decide if translation is needed
            if client_lang == target_language:
                final_text = text
                logging.debug(f"[Server] Client {client_id}: No translation needed (already '{target_language}').")
                sync_manager.update_client_phase(client_id, PHASE_CHECKED)
                sync_manager.update_client_phase(client_id, PHASE_READY)
            else:
                sync_manager.update_client_phase(client_id, PHASE_CHECKED)
                sync_manager.update_client_phase(client_id, PHASE_STARTED_TRANSLATION)
                final_text = translate_text(text, source_lang=client_lang, target_lang=target_language)
                time.sleep(1)  # Simulate processing delay
                sync_manager.update_client_phase(client_id, PHASE_ENDED_TRANSLATION)
                sync_manager.update_client_phase(client_id, PHASE_READY)

            # Check if all active clients are ready
            if sync_manager.all_clients_ready_for(active_client_ids):
                logging.info("[Server] Barrier reached: all active clients are ready. Broadcasting final message.")
                broadcast_message(f"MSG|{final_text}")
                # Reset only these active clients
                sync_manager.reset_clients(active_client_ids)
            else:
                logging.debug("[Server] Waiting for barrier: not all active clients are ready.")

    except Exception as e:
        logging.error(f"[Server] Exception in client {client_id} handler: {e}")
    finally:
        conn.close()
        with client_lock:
            if client_id in clients:
                del clients[client_id]
        sync_manager.remove_client(client_id)
        logging.info(f"[Server] Connection with client {client_id} closed.")

def client_acceptor(server_sock, context, target_language):
    global client_id_counter
    while True:
        try:
            client_sock, addr = server_sock.accept()
            tls_conn = context.wrap_socket(client_sock, server_side=True)
            with client_lock:
                client_id_counter += 1
                client_id = client_id_counter
                clients[client_id] = tls_conn

            # New clients start waiting
            sync_manager.update_client_phase(client_id, PHASE_WAITING)
            threading.Thread(
                target=handle_client,
                args=(tls_conn, addr, client_id, target_language),
                daemon=True
            ).start()
        except Exception as e:
            logging.error(f"[Server] Error accepting client connection: {e}")

def main():
    # 1. Generate a certificate/key if needed
    generate_self_signed_cert_if_needed()

    # 2. Prompt for target language
    target_language = input("Enter target language for translation (e.g., 'en'): ").strip().lower()
    if not target_language:
        target_language = 'en'
    logging.info(f"[Server] Target language set to: {target_language}")

    # 3. Create/bind socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((SERVER_HOST, SERVER_PORT))
    sock.listen(5)
    logging.info(f"[Server] Listening on {SERVER_HOST}:{SERVER_PORT}")

    # 4. Create SSL context
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

    # 5. Start acceptor
    threading.Thread(target=client_acceptor, args=(sock, context, target_language), daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("[Server] Shutting down.")

if __name__ == '__main__':
    main()
