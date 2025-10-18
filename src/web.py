from flask import Flask, render_template, request, jsonify
import threading
import os
import time
from typing import List

from src.players import Player, load_players, save_players
from src.simulator import Simulator

DEFAULT_PLAYERS_FILE = os.path.join("data", "players.json")

# Create Flask app with templates folder in project root
app = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'templates'))

def create_sample_players(n: int = 8) -> List[Player]:
    return [Player(id=i + 1, name=f"Player_{i+1}") for i in range(n)]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/init', methods=['POST'])
def api_init():
    try:
        players = create_sample_players(8)
        save_players(DEFAULT_PLAYERS_FILE, players)
        return jsonify({'status': 'ok', 'message': f'Created sample players at {DEFAULT_PLAYERS_FILE}'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/top', methods=['GET'])
def api_top():
    players = load_players(DEFAULT_PLAYERS_FILE)
    if not players:
        return jsonify({'status': 'error', 'message': 'No players found'}), 404
    players_sorted = sorted(players, key=lambda p: -p.rating)
    data = [{'id': p.id, 'name': p.name, 'rating': p.rating} for p in players_sorted[:20]]
    return jsonify({'status': 'ok', 'top': data})

@app.route('/api/run', methods=['POST'])
def api_run():
    payload = request.get_json() or {}
    matches = int(payload.get('matches', 100))
    seed = payload.get('seed', None)
    k = float(payload.get('k', 32.0))
    arcade = bool(payload.get('arcade', False))
    streak = float(payload.get('streak', 0.0))
    decay = float(payload.get('decay', 0.0))

    try:
        players = load_players(DEFAULT_PLAYERS_FILE)
        if not players:
            players = create_sample_players(8)

        sim = Simulator(players=players, k=k, arcade_mode=arcade, streak_bonus_pct=streak, decay_per_day=decay)
        records = sim.run_batch(matches=matches, seed=(None if seed in (None, '') else int(seed)))
        sim.apply_decay(inactive_seconds=30 * 24 * 3600)
        save_players(DEFAULT_PLAYERS_FILE, players)

        players_sorted = sorted(players, key=lambda p: -p.rating)
        top = [{'id': p.id, 'name': p.name, 'rating': p.rating} for p in players_sorted[:10]]
        return jsonify({'status': 'ok', 'matches': len(records), 'top': top}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def run_web(host: str = '127.0.0.1', port: int = 5000, debug: bool = False):
    print(f"Starting web UI at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_web()