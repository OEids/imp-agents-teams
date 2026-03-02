"""
Simple Flask server for the AI Agent Office Visualization.
Serves the static HTML and provides the /api/employee-status endpoint.
"""

from flask import Flask, jsonify, send_from_directory
import random
import time

app = Flask(__name__, static_folder='.')

# Agent definitions matching the frontend
agents = [
    {'id': 'researcher', 'name': 'Researcher', 'status': 'working'},
    {'id': 'writer', 'name': 'Writer', 'status': 'working'},
    {'id': 'developer', 'name': 'Developer', 'status': 'working'},
    {'id': 'designer', 'name': 'Designer', 'status': 'idle'},
    {'id': 'video', 'name': 'Video', 'status': 'working'},
    {'id': 'motion', 'name': 'Motion', 'status': 'idle'},
    {'id': 'qa', 'name': 'QA', 'status': 'working'},
    {'id': 'scout', 'name': 'Scout', 'status': 'working'}
]

# Track last status change time
last_change = time.time()


@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('.', 'index.html')


@app.route('/api/employee-status')
def employee_status():
    """
    Return current status of all agents.
    In a real implementation, this would query your actual AI agents.
    For demo purposes, it randomly changes statuses occasionally.
    """
    global last_change

    # Randomly change a status every ~15 seconds for demo
    if time.time() - last_change > 15:
        agent = random.choice(agents)
        agent['status'] = 'idle' if agent['status'] == 'working' else 'working'
        last_change = time.time()
        print(f"[Status Change] {agent['name']} is now {agent['status']}")

    return jsonify(agents)


@app.route('/api/set-status/<agent_id>/<status>')
def set_status(agent_id, status):
    """
    Manually set an agent's status.
    Usage: GET /api/set-status/developer/idle
    """
    if status not in ['working', 'idle']:
        return jsonify({'error': 'Status must be "working" or "idle"'}), 400

    for agent in agents:
        if agent['id'] == agent_id:
            agent['status'] = status
            print(f"[Manual] {agent['name']} set to {status}")
            return jsonify({'success': True, 'agent': agent})

    return jsonify({'error': f'Agent {agent_id} not found'}), 404


@app.route('/api/all-working')
def all_working():
    """Set all agents to working status."""
    for agent in agents:
        agent['status'] = 'working'
    return jsonify({'success': True, 'agents': agents})


@app.route('/api/all-idle')
def all_idle():
    """Set all agents to idle status."""
    for agent in agents:
        agent['status'] = 'idle'
    return jsonify({'success': True, 'agents': agents})


if __name__ == '__main__':
    print("\n" + "="*50)
    print("  AI AGENT OFFICE VISUALIZATION SERVER")
    print("="*50)
    print("\n  Open http://localhost:5000 in your browser")
    print("\n  API Endpoints:")
    print("    GET /api/employee-status - Get all agent statuses")
    print("    GET /api/set-status/<id>/<status> - Set agent status")
    print("    GET /api/all-working - Set all to working")
    print("    GET /api/all-idle - Set all to idle")
    print("\n" + "="*50 + "\n")

    app.run(debug=True, port=5000)
