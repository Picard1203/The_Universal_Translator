# server/sync_manager.py
import threading
import logging

# Define phase constants
PHASE_WAITING = 0           # Waiting for a new message
PHASE_SENT = 1              # Message sent by client
PHASE_RECEIVED = 2          # Message received by server
PHASE_CHECKED = 3           # Language checked
PHASE_STARTED_TRANSLATION = 4
PHASE_ENDED_TRANSLATION = 5
PHASE_READY = 6             # Ready to broadcast

class SyncManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.client_phases = {}  # Mapping: client_id -> phase (int)

    def update_client_phase(self, client_id, phase):
        with self.lock:
            self.client_phases[client_id] = phase
            logging.debug(f"[SyncManager] Client {client_id} updated to phase {phase}.")

    def remove_client(self, client_id):
        with self.lock:
            if client_id in self.client_phases:
                del self.client_phases[client_id]
                logging.debug(f"[SyncManager] Removed client {client_id}.")

    def get_status(self):
        with self.lock:
            return dict(self.client_phases)

    def all_clients_ready(self):
        with self.lock:
            if not self.client_phases:
                return False
            return all(phase >= PHASE_READY for phase in self.client_phases.values())

    def all_clients_ready_for(self, client_list):
        with self.lock:
            for cid in client_list:
                if cid in self.client_phases:
                    if self.client_phases[cid] < PHASE_READY:
                        return False
            return True

    def reset_clients(self, client_list):
        with self.lock:
            for cid in client_list:
                if cid in self.client_phases:
                    self.client_phases[cid] = PHASE_WAITING
                    logging.debug(f"[SyncManager] Reset client {cid} to phase {PHASE_WAITING}.")

# Global instance
sync_manager = SyncManager()

# Expose constants for import
PHASE_WAITING = PHASE_WAITING
PHASE_SENT = PHASE_SENT
PHASE_RECEIVED = PHASE_RECEIVED
PHASE_CHECKED = PHASE_CHECKED
PHASE_STARTED_TRANSLATION = PHASE_STARTED_TRANSLATION
PHASE_ENDED_TRANSLATION = PHASE_ENDED_TRANSLATION
PHASE_READY = PHASE_READY
