"""
CLI entry point for running simulations.
"""
import argparse
from src.players import load_players, save_players, Player
from src.simulator import Simulator
import json
import os
import sys

DEFAULT_PLAYERS_FILE = os.path.join("data", "players.json")

def ensure_data_dir():
    os.makedirs("data", exist_ok=True)

def create_sample_players(n: int = 8):
    return [Player(id=i+1, name=f"Player_{i+1}") for i in range(n)]

def main(argv=None):
    parser = argparse.ArgumentParser(description="Rank/ELO Simulator")
    parser.add_argument("--players-file", "-p", default=DEFAULT_PLAYERS_FILE,
                        help="Path to players.json")
    parser.add_argument("--matches", "-m", type=int, default=1000,
                        help="Number of matches to simulate")
    parser.add_argument("--k", type=float, default=32.0, help="ELO K-factor")
    parser.add_argument("--arcade", action="store_true", help="Enable win-streak arcade bonus")
    parser.add_argument("--streak-bonus", type=float, default=0.0,
                        help="Per-win-streak bonus fraction (e.g. 0.1 for 10 percent)")
    parser.add_argument("--decay-per-day", type=float, default=0.0,
                        help="Rating decay applied per inactive day")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--init", action="store_true",
                        help="Create sample players file if missing")
    args = parser.parse_args(argv)

    ensure_data_dir()

    if args.init or not os.path.exists(args.players_file):
        players = create_sample_players(8)
        save_players(args.players_file, players)
        print(f"Created sample players at {args.players_file}")
        return

    players = load_players(args.players_file)
    if not players:
        print("No players loaded. Use --init to create sample players.", file=sys.stderr)
        return

    sim = Simulator(players=players, k=args.k, arcade_mode=args.arcade,
                    streak_bonus_pct=args.streak_bonus, decay_per_day=args.decay_per_day)
    records = sim.run_batch(matches=args.matches, seed=args.seed)
    # Optionally apply decay to those inactive for 30 days (example)
    sim.apply_decay(inactive_seconds=30 * 24 * 3600)

    # Save players back to file
    save_players(args.players_file, players)
    print(f"Simulated {len(records)} matches. Players saved to {args.players_file}")

if __name__ == "__main__":
    main()
