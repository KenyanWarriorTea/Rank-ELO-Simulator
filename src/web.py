from __future__ import annotations

import json
import os
import tempfile
import time
from typing import List

from flask import Flask, jsonify, render_template, request, send_file

from src.players import Player, load_players, save_players

DEFAULT_PLAYERS_FILE = os.path.join("data", "players.json")

app = Flask(__name__, template_folder=os.path.join(os.getcwd(), "templates"))


def ensure_data_dir() -> None:
    """Ensure data directory exists."""
    os.makedirs("data", exist_ok=True)


def create_sample_players(n: int = 8) -> List[Player]:
    """Create n sample Player objects."""
    return [Player(id=i + 1, name=f"Player_{i+1}") for i in range(n)]


@app.route("/")
def index() -> str:
    """Serve main UI."""
    return render_template("index.html")


@app.route("/api/init", methods=["POST"])
def api_init() -> tuple[dict, int]:
    """Initialize players file with sample players."""
    try:
        ensure_data_dir()
        players = create_sample_players(8)
        save_players(DEFAULT_PLAYERS_FILE, players)
        return {"status": "ok", "message": "Created 8 sample players"}, 200
    except Exception as exc:  # pragma: no cover - top-level error handler
        app.logger.exception("Error in api_init")
        return {"status": "error", "message": "Failed to initialize players"}, 500


@app.route("/api/top", methods=["GET"])
def api_top() -> tuple[dict, int]:
    """Return top players (by rating)."""
    try:
        players = load_players(DEFAULT_PLAYERS_FILE)
        if not players:
            return {"status": "ok", "top": []}, 200
        players_sorted = sorted(players, key=lambda p: -p.rating)
        data = [
            {
                "id": p.id,
                "name": p.name,
                "rating": p.rating,
                "tier": p.tier,
                "win_streak": p.win_streak,
            }
            for p in players_sorted[:20]
        ]
        return {"status": "ok", "top": data}, 200
    except Exception:  # pragma: no cover
        app.logger.exception("Error in api_top")
        return {"status": "error", "message": "Failed to load top players"}, 500


@app.route("/api/players", methods=["GET"])
def api_players_list() -> tuple[dict, int]:
    """Return full players list."""
    try:
        players = load_players(DEFAULT_PLAYERS_FILE)
        if not players:
            return {"status": "ok", "players": []}, 200
        players_sorted = sorted(players, key=lambda p: -p.rating)
        data = [
            {
                "id": p.id,
                "name": p.name,
                "rating": p.rating,
                "tier": p.tier,
                "win_streak": p.win_streak,
                "history": p.history,
            }
            for p in players_sorted
        ]
        return {"status": "ok", "players": data}, 200
    except Exception:  # pragma: no cover
        app.logger.exception("Error in api_players_list")
        return {"status": "error", "message": "Failed to load players"}, 500


@app.route("/api/players", methods=["POST"])
def api_add_player() -> tuple[dict, int]:
    """Add a new player via JSON payload {name, rating}."""
    try:
        payload = request.get_json() or {}
        name = (payload.get("name") or "").strip()
        rating = float(payload.get("rating", 1500.0))

        if not name:
            return {"status": "error", "message": "Player name is required"}, 400

        ensure_data_dir()
        players = load_players(DEFAULT_PLAYERS_FILE)
        max_id = max((p.id for p in players), default=0)
        new_player = Player(id=max_id + 1, name=name, rating=rating)
        players.append(new_player)
        save_players(DEFAULT_PLAYERS_FILE, players)
        return {"status": "ok", "message": f"Added player {name}", "player": new_player.to_dict()}, 200
    except Exception:  # pragma: no cover
        app.logger.exception("Error in api_add_player")
        return {"status": "error", "message": "Failed to add player"}, 500


@app.route("/api/analytics", methods=["GET"])
def api_analytics() -> tuple[dict, int]:
    """Simple analytics: counts, avg rating, distribution buckets."""
    try:
        players = load_players(DEFAULT_PLAYERS_FILE)
        if not players:
            return {
                "status": "ok",
                "data": {
                    "total_players": 0,
                    "avg_rating": 0,
                    "highest_rating": 0,
                    "total_matches": 0,
                    "rating_distribution": {"labels": [], "counts": []},
                },
            }, 200

        total_players = len(players)
        avg_rating = sum(p.rating for p in players) / total_players
        highest_rating = max(p.rating for p in players)
        total_matches = sum(len(p.history) for p in players) // 2

        buckets: dict[int, int] = {}
        for p in players:
            bucket = int(p.rating // 100) * 100
            buckets[bucket] = buckets.get(bucket, 0) + 1

        sorted_buckets = sorted(buckets.items())
        labels = [f"{b}-{b+99}" for b, _ in sorted_buckets]
        counts = [c for _, c in sorted_buckets]

        return {
            "status": "ok",
            "data": {
                "total_players": total_players,
                "avg_rating": avg_rating,
                "highest_rating": highest_rating,
                "total_matches": total_matches,
                "rating_distribution": {"labels": labels, "counts": counts},
            },
        }, 200
    except Exception:  # pragma: no cover
        app.logger.exception("Error in api_analytics")
        return {"status": "error", "message": "Failed to load analytics"}, 500


@app.route("/api/run", methods=["POST"])
def api_run() -> tuple[dict, int]:
    """Run a batch simulation (delegates to Simulator if available)."""
    payload = request.get_json() or {}
    matches = int(payload.get("matches", 100))
    seed = payload.get("seed", None)
    k = float(payload.get("k", 32.0))
    arcade = bool(payload.get("arcade", False))
    streak = float(payload.get("streak", 0.0))
    decay = float(payload.get("decay", 0.0))

    try:
        ensure_data_dir()
        players = load_players(DEFAULT_PLAYERS_FILE)
        if not players:
            players = create_sample_players(8)

        # Import Simulator here to avoid hard import if module missing
        from src.simulator import Simulator

        sim = Simulator(players=players, k=k, arcade_mode=arcade, streak_bonus_pct=streak, decay_per_day=decay)
        records = sim.run_batch(matches=matches, seed=seed)
        save_players(DEFAULT_PLAYERS_FILE, players)

        players_sorted = sorted(players, key=lambda p: -p.rating)
        top = [
            {"id": p.id, "name": p.name, "rating": p.rating, "tier": p.tier, "win_streak": p.win_streak}
            for p in players_sorted[:10]
        ]
        return {"status": "ok", "matches": len(records), "top": top}, 200
    except Exception:  # pragma: no cover
        app.logger.exception("Error in api_run")
        return {"status": "error", "message": "Failed to run simulation"}, 500


@app.route("/api/reset", methods=["POST"])
def api_reset() -> tuple[dict, int]:
    """Reset (remove) players file."""
    try:
        if os.path.exists(DEFAULT_PLAYERS_FILE):
            os.remove(DEFAULT_PLAYERS_FILE)
        return {"status": "ok", "message": "All data reset successfully"}, 200
    except Exception:  # pragma: no cover
        app.logger.exception("Error in api_reset")
        return {"status": "error", "message": "Failed to reset data"}, 500


@app.route("/api/export", methods=["GET"])
def api_export() -> tuple:
    """Export players as JSON file (temporary file returned)."""
    try:
        players = load_players(DEFAULT_PLAYERS_FILE)
        export_data = {"players": [p.to_dict() for p in players], "exported_at": time.time(), "total_players": len(players)}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmpf:
            json.dump(export_data, tmpf, indent=2)
            temp_path = tmpf.name

        # send_file will stream the file; we do not delete it here immediately
        return send_file(temp_path, as_attachment=True, download_name=f"elo-simulation-{int(time.time())}.json", mimetype="application/json")
    except Exception:  # pragma: no cover
        app.logger.exception("Error in api_export")
        return jsonify({"status": "error", "message": "Failed to export data"}), 500


def run_web(host: str = "127.0.0.1", port: int = 5000, debug: bool = False) -> None:
    """Start Flask development server."""
    ensure_data_dir()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":  # pragma: no cover - start server when executed directly
    run_web(debug=True)
