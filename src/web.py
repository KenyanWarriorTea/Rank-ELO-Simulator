from flask import Flask, render_template, request, jsonify, send_file
import threading
import os
import time
import json
from typing import List

from src.players import Player, load_players, save_players
from src.simulator import Simulator

DEFAULT_PLAYERS_FILE = os.path.join("data", "players.json")

# Create Flask app with templates folder in project root
app = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'templates'))

def ensure_data_dir():
    os.makedirs("data", exist_ok=True)

def create_sample_players(n: int = 8) -> List[Player]:
    return [Player(id=i + 1, name=f"Player_{i+1}") for i in range(n)]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/init', methods=['POST'])
def api_init():
    try:
        ensure_data_dir()
        players = create_sample_players(8)
        save_players(DEFAULT_PLAYERS_FILE, players)
        return jsonify({'status': 'ok', 'message': f'Created 8 sample players'}), 200
    except Exception as e:
        app.logger.error(f"Error in api_init: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to initialize players'}), 500

@app.route('/api/top', methods=['GET'])
def api_top():
    try:
        players = load_players(DEFAULT_PLAYERS_FILE)
        if not players:
            return jsonify({'status': 'ok', 'top': []}), 200
        players_sorted = sorted(players, key=lambda p: -p.rating)
        data = [{'id': p.id, 'name': p.name, 'rating': p.rating, 'tier': p.tier, 'win_streak': p.win_streak} for p in players_sorted[:20]]
        return jsonify({'status': 'ok', 'top': data})
    except Exception as e:
        app.logger.error(f"Error in api_top: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to load top players'}), 500

@app.route('/api/players', methods=['GET'])
def api_players_list():
    try:
        players = load_players(DEFAULT_PLAYERS_FILE)
        if not players:
            return jsonify({'status': 'ok', 'players': []}), 200
        players_sorted = sorted(players, key=lambda p: -p.rating)
        data = [{'id': p.id, 'name': p.name, 'rating': p.rating, 'tier': p.tier, 'win_streak': p.win_streak, 'history': p.history} for p in players_sorted]
        return jsonify({'status': 'ok', 'players': data})
    except Exception as e:
        app.logger.error(f"Error in api_players_list: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to load players'}), 500

@app.route('/api/players', methods=['POST'])
def api_add_player():
    try:
        payload = request.get_json() or {}
        name = payload.get('name', '').strip()
        rating = float(payload.get('rating', 1500.0))
        
        if not name:
            return jsonify({'status': 'error', 'message': 'Player name is required'}), 400
        
        ensure_data_dir()
        players = load_players(DEFAULT_PLAYERS_FILE)
        
        # Find next available ID
        max_id = max([p.id for p in players], default=0)
        new_player = Player(id=max_id + 1, name=name, rating=rating)
        players.append(new_player)
        
        save_players(DEFAULT_PLAYERS_FILE, players)
        return jsonify({'status': 'ok', 'message': f'Added player {name}', 'player': new_player.to_dict()}), 200
    except Exception as e:
        app.logger.error(f"Error in api_add_player: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to add player'}), 500

@app.route('/api/analytics', methods=['GET'])
def api_analytics():
    try:
        players = load_players(DEFAULT_PLAYERS_FILE)
        if not players:
            return jsonify({
                'status': 'ok',
                'data': {
                    'total_players': 0,
                    'avg_rating': 0,
                    'highest_rating': 0,
                    'total_matches': 0,
                    'rating_distribution': {'labels': [], 'counts': []}
                }
            }), 200
        
        total_players = len(players)
        avg_rating = sum(p.rating for p in players) / total_players
        highest_rating = max(p.rating for p in players)
        total_matches = sum(len(p.history) for p in players) // 2  # Divide by 2 since each match is counted twice
        
        # Rating distribution (buckets of 100)
        buckets = {}
        for p in players:
            bucket = int(p.rating // 100) * 100
            buckets[bucket] = buckets.get(bucket, 0) + 1
        
        sorted_buckets = sorted(buckets.items())
        labels = [f"{b}-{b+99}" for b, _ in sorted_buckets]
        counts = [c for _, c in sorted_buckets]
        
        return jsonify({
            'status': 'ok',
            'data': {
                'total_players': total_players,
                'avg_rating': avg_rating,
                'highest_rating': highest_rating,
                'total_matches': total_matches,
                'rating_distribution': {'labels': labels, 'counts': counts}
            }
        }), 200
    except Exception as e:
        app.logger.error(f"Error in api_analytics: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to load analytics'}), 500

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
        ensure_data_dir()
        players = load_players(DEFAULT_PLAYERS_FILE)
        if not players:
            players = create_sample_players(8)

        sim = Simulator(players=players, k=k, arcade_mode=arcade, streak_bonus_pct=streak, decay_per_day=decay)
        records = sim.run_batch(matches=matches, seed=(None if seed in (None, '') else int(seed)))
        sim.apply_decay(inactive_seconds=30 * 24 * 3600)
        save_players(DEFAULT_PLAYERS_FILE, players)

        players_sorted = sorted(players, key=lambda p: -p.rating)
        top = [{'id': p.id, 'name': p.name, 'rating': p.rating, 'tier': p.tier, 'win_streak': p.win_streak} for p in players_sorted[:10]]
        return jsonify({'status': 'ok', 'matches': len(records), 'top': top}), 200
    except Exception as e:
        app.logger.error(f"Error in api_run: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to run simulation'}), 500

@app.route('/api/reset', methods=['POST'])
def api_reset():
    try:
        if os.path.exists(DEFAULT_PLAYERS_FILE):
            os.remove(DEFAULT_PLAYERS_FILE)
        return jsonify({'status': 'ok', 'message': 'All data reset successfully'}), 200
    except Exception as e:
        app.logger.error(f"Error in api_reset: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to reset data'}), 500

@app.route('/api/export', methods=['GET'])
def api_export():
    try:
        players = load_players(DEFAULT_PLAYERS_FILE)
        export_data = {
            'players': [p.to_dict() for p in players],
            'exported_at': time.time(),
            'total_players': len(players)
        }
        
        # Create temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(export_data, f, indent=2)
            temp_path = f.name
        
        return send_file(temp_path, as_attachment=True, download_name=f'elo-simulation-{int(time.time())}.json', mimetype='application/json')
    except Exception as e:
        app.logger.error(f"Error in api_export: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to export data'}), 500


def run_web(host: str = '127.0.0.1', port: int = 5000, debug: bool = False):
    print(f"Starting web UI at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_web()