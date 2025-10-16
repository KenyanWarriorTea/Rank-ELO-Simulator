# 🎮 Rank/ELO Simulator

A lightweight simulation engine for ranking systems used in competitive games (similar to Elo in chess or MMR in online games like League of Legends, Valorant, Dota 2 and CS2).

This project simulates rating progression between players, visualizes how ratings evolve through repeated matches, and demonstrates how matchmaking systems work internally.

---

##  Features

-  **Player-based rating model (MMR/ELO)**
-  **Match simulation: Player vs Player**
-  **Rating updates based on classic Elo formula**
-  **Optional win streak bonus (Arcade Mode)**
-  **Rating decay for inactive players**
-  **Batch simulation mode — run 1000+ matches automatically**
-  **(Planned)** Data export to JSON / CSV for visualization

---

##  Project Structure

rank-elo-simulator/
│
├── src/
│ ├── players.py # Player class with MMR tracking
│ ├── elo_system.py # Elo formula and rating adjustment logic
│ ├── simulator.py # Batch simulation logic
│ └── main.py # Entry point (CLI)
│
├── data/
│ ├── players.json # Player data / simulation history
│
├── README.md # Documentation (you are here)
└── LICENSE # 

What This Project Demonstrates

This project is perfect for showcasing:

Understanding of ranking algorithms used in real games.

Ability to write clean and modular Python code.

Game systems design thinking (MMR distribution, fairness, progression).

Open-source readiness: documentation, repository structure, code clarity.

