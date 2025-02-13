# client/sync.py
import threading
import logging

logging.basicConfig(level=logging.DEBUG)

PHASE_WAITING = 0
PHASE_SENT = 1
PHASE_RECEIVED = 2
PHASE_CHECKED = 3
PHASE_STARTED_TRANSLATION = 4
PHASE_ENDED_TRANSLATION = 5
PHASE_READY = 6

class VectorClock:
    def __init__(self, client_id, total_clients):
        self.client_id = client_id
        self.clock = [PHASE_WAITING] * total_clients
        self.lock = threading.Lock()

    def update_phase(self, client_index, phase):
        with self.lock:
            self.clock[client_index] = phase
            logging.debug(f"[VectorClock] Client {client_index} updated to phase {phase}.")

    def get_clock(self):
        with self.lock:
            return list(self.clock)

class Barrier:
    def __init__(self, total_clients):
        self.total_clients = total_clients
        self.counter = 0
        self.condition = threading.Condition()

    def wait(self):
        with self.condition:
            self.counter += 1
            if self.counter >= self.total_clients:
                self.condition.notify_all()
                self.counter = 0  # Reset for next barrier
            else:
                self.condition.wait()
