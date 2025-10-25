"""
Lightweight Flask web UI / API for Rank/ELO Simulator.

Endpoints:
 - GET  /           -> serves index.html (template)
 - POST /api/init   -> create sample players (if missing)
 - POST /api/run    -> run simulation with parameters
 - GET  /api/top    -> return top players (without running)

This module prefers explicit, defensive parsing of inputs and returns
JSON with helpful error messages on failure.
"""
from typing import Any, Dict, List, Optional
import os
import logging

from flask import Flask, jsonify, render_template, request

from src.simulator import Simulator
from src.players import load_players, save_players
from src.main import create_sample_players

# default players file (relative to project root)
DEFAULT_PLAYERS_FILE = os.path.join("data", "players.json")

app = Flask(__name__, template_folder=os.path.join(
    os.path.dirname(__file__), "..", "templates"
))
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@app.route("/")
def index() -> Any:
    """Serve the UI page."""
    return render_template("index.html")


@app.route("/api/init", methods=["POST"])
def api_init() -> Any:
    """Create and save sample players (overwrites only if missing)."""
    try:
        players = load_players(DEFAULT_PLAYERS_FILE)
        if players:
            return jsonify({"status": "ok", "message": "Players file already exists"}), 200
        players = create_sample_players(8)
        save_players(DEFAULT_PLAYERS_FILE, players)
        return jsonify({"status": "ok", "message": "Sample players created"}), 201
    except Exception as exc:  # pragma: no cover - top-level safety
        logger.exception("Failed to init players")
        return jsonify({"status": "error", "message": str(exc)}), 500


def players_to_top(players: List[Any], count: int = 10) -> List[Dict[str, Any]]:
    """Convert players list to simple top representation for UI."""
    top: List[Dict[str, Any]] = []
    for p in sorted(players, key=lambda x: -getattr(x, "rating", 0.0))[:count]:
        tier = getattr(p, "tier", None) or {}
        top.append({
            "id": getattr(p, "id", None),
            "name": getattr(p, "name", "Player"),
            "rating": float(getattr(p, "rating", 0.0)),
            "wins": getattr(p, "wins", 0),
            "tier": {
                "tier": tier.get("tier") if isinstance(tier, dict) else None,
                "division": tier.get("division") if isinstance(tier, dict) else None,
                "color": tier.get("color") if isinstance(tier, dict) else None,
            },
        })
    return top


@app.route("/api/top", methods=["GET"])
def api_top() -> Any:
    """Return the top players currently in players.json."""
    try:
        players = load_players(DEFAULT_PLAYERS_FILE) or []
        return jsonify({"status": "ok", "top": players_to_top(players)}), 200
    except Exception as exc:
        logger.exception("Failed to load top")
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/run", methods=["POST"])
def api_run() -> Any:
    """
    Run a simulation batch.

    Expected JSON payload:
      {matches:int, seed:(int|string|null), k:float, arcade:bool, streak:float, decay:float}
    """
    payload = request.get_json(silent=True) or {}
    # defensive parsing with defaults
    try:
        matches = int(payload.get("matches", 100))
    except (TypeError, ValueError):
        matches = 100

    seed_raw = payload.get("seed", None)
    seed: Optional[int] = None
    # allow empty string to mean None; if numeric string -> int; if non-numeric -> leave as None
    if seed_raw in (None, ""):
        seed = None
    else:
        try:
            seed = int(seed_raw)
        except (TypeError, ValueError):
            # non-integer seed: leave as None and let simulator use randomness
            seed = None

    try:
        k = float(payload.get("k", 32.0))
    except (TypeError, ValueError):
        k = 32.0

    arcade = bool(payload.get("arcade", False))
    try:
        streak = float(payload.get("streak", 0.0))
    except (TypeError, ValueError):
        streak = 0.0
    try:
        decay = float(payload.get("decay", 0.0))
    except (TypeError, ValueError):
        decay = 0.0

    try:
        players = load_players(DEFAULT_PLAYERS_FILE)
        if not players:
            # fallback: create sample players (non-destructive)
            players = create_sample_players(8)

        sim = Simulator(players=players, k=k, arcade_mode=arcade,
                        streak_bonus_pct=streak, decay_per_day=decay)
        records = sim.run_batch(matches=matches, seed=seed)
        # periodic decay example (30 days)
        sim.apply_decay(inactive_seconds=30 * 24 * 3600)
        save_players(DEFAULT_PLAYERS_FILE, players)

        top = players_to_top(players, count=10)
        return jsonify({"status": "ok", "matches": len(records), "top": top}), 200
    except Exception as exc:  # pragma: no cover - keep robust for user runs
        logger.exception("Simulation failed")
        return jsonify({"status": "error", "message": str(exc)}), 500


def run_web(host: str = "127.0.0.1", port: int = 5000, debug: bool = False) -> None:
    """Convenience: start the Flask web server."""
    logger.info("Starting web UI at http://%s:%s", host, port)
    app.run(host=host, port=port, debug=debug)