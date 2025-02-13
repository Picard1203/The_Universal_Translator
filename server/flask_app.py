# server/flask_app.py
from flask import Flask, request, jsonify
from sync_manager import sync_manager
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

@app.route('/update_sync', methods=['POST'])
def update_sync():
    data = request.get_json()
    client_id = data.get('client_id')
    phase = data.get('phase')
    if client_id is None or phase is None:
        return jsonify({'error': 'client_id and phase are required'}), 400
    sync_manager.update_client_phase(client_id, phase)
    all_ready = sync_manager.all_clients_ready()
    return jsonify({'all_ready': all_ready, 'sync_status': sync_manager.get_status()}), 200

@app.route('/get_sync_status', methods=['GET'])
def get_sync_status():
    return jsonify(sync_manager.get_status()), 200

if __name__ == '__main__':
    # Run the Flask API on port 5002.
    app.run(host='0.0.0.0', port=5002, debug=True)
