#  Rank/ELO Simulator

A lightweight simulation engine for ranking systems used in competitive games (similar to Elo in chess or MMR in online games like League of Legends, Valorant, Dota 2 and CS2).

This project simulates rating progression between players, visualizes how ratings evolve through repeated matches, and demonstrates how matchmaking systems work internally.

---

##  Features

### Core Simulation
-  **Player-based rating model (MMR/ELO)**
-  **Match simulation: Player vs Player**
-  **Rating updates based on classic Elo formula**
-  **Optional win streak bonus (Arcade Mode)**
-  **Rating decay for inactive players**
-  **Batch simulation mode — run 1000+ matches automatically**

### Web Interface
-  **Modern, responsive UI with dark/light mode**
-  **Three-tab interface: Simulator, Players, Analytics**
-  **Real-time simulation with progress indicator**
-  **Player management (add custom players, view stats)**
-  **Analytics dashboard with rating distribution charts**
-  **Export data to JSON**
-  **Persistent theme preferences**

### CLI Interface
-  **Command-line interface for batch processing**
-  **Configurable parameters (K-factor, arcade mode, decay)**
-  **Random seed support for reproducible results**

---

##  Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/KenyanWarriorTea/Rank-ELO-Simulator.git
cd Rank-ELO-Simulator

# Install dependencies
pip install -r requirements.txt
```

### Web Interface

```bash
# Start the web server
python -m src.web

# Open your browser to http://localhost:5000
```

### Command Line Interface

```bash
# Initialize sample players
python -m src.main --init

# Run 1000 matches
python -m src.main --matches 1000

# Run with arcade mode and streak bonus
python -m src.main --matches 500 --arcade --streak-bonus 0.1

# Run with specific K-factor and seed
python -m src.main --matches 100 --k 40 --seed 42
```

---

##  Project Structure

```
rank-elo-simulator/
│
├── src/
│   ├── players.py          # Player class with MMR tracking
│   ├── elo_system.py       # Elo formula and rating adjustment logic
│   ├── ranks.py            # Tier system (Iron to Challenger)
│   ├── simulator.py        # Batch simulation logic
│   ├── main.py             # CLI entry point
│   └── web.py              # Web interface (Flask)
│
├── templates/
│   └── index.html          # Modern web UI with tabs and charts
│
├── data/
│   └── players.json        # Player data / simulation history
│
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
├── README.md              # Documentation
└── LICENSE                # MIT License
```

---

##  CLI Options

```
usage: main.py [-h] [--players-file PLAYERS_FILE] [--matches MATCHES] [--k K] 
               [--arcade] [--streak-bonus STREAK_BONUS] 
               [--decay-per-day DECAY_PER_DAY] [--seed SEED] [--init]

options:
  -h, --help            show this help message and exit
  --players-file, -p    Path to players.json (default: data/players.json)
  --matches, -m         Number of matches to simulate (default: 1000)
  --k                   ELO K-factor (default: 32.0)
  --arcade              Enable win-streak arcade bonus
  --streak-bonus        Per-win-streak bonus fraction (default: 0.0)
  --decay-per-day       Rating decay applied per inactive day (default: 0.0)
  --seed                Random seed for reproducibility
  --init                Create sample players file
```

---

##  Web Interface Guide

### Simulator Tab
- **Configure simulation parameters**: matches, K-factor, arcade mode, streak bonus, decay
- **Run simulations**: Execute batch matches with visual progress
- **View top players**: See leaderboard with tier badges and ratings
- **Activity log**: Monitor simulation events in real-time

### Players Tab
- **Add players**: Create custom players with specific starting ratings
- **View all players**: See complete roster with stats (streaks, match count)
- **Player details**: Each player shows tier, rating, and match history

### Analytics Tab
- **Key metrics**: Total players, average rating, highest rating, total matches
- **Rating distribution**: Bar chart showing player spread across rating ranges
- **Visual insights**: Understand your simulation's competitive landscape

---

##  Tier System

The simulator uses a League of Legends-inspired tier system:

| Tier | Rating Range | Color |
|------|-------------|-------|
| Iron | 1000-1099 | Gray |
| Bronze | 1100-1199 | Bronze |
| Silver | 1200-1299 | Silver |
| Gold | 1300-1399 | Gold |
| Platinum | 1400-1549 | Cyan |
| Diamond | 1550-1699 | Blue |
| Master | 1700-1849 | Purple |
| Grandmaster | 1850-1999 | Red |
| Challenger | 2000+ | Orange |

Each tier (except Master+) has 4 divisions: IV (lowest) to I (highest).

---

##  What This Project Demonstrates

This project is perfect for showcasing:

- **Understanding of ranking algorithms** used in real competitive games
- **Clean, modular Python code** with proper separation of concerns
- **Modern web development** with Flask backend and responsive frontend
- **Game systems design thinking** (MMR distribution, fairness, progression)
- **Data visualization** with charts and statistics
- **Full-stack development** skills (backend API, frontend UI, CLI tools)
- **Security best practices** (proper error handling, no information leakage)
- **Open-source readiness**: documentation, repository structure, code clarity

---

##  Examples

### Simulate competitive season
```bash
# Initialize 16 players
python -m src.main --init

# Run a full season (1000 matches)
python -m src.main --matches 1000 --k 32

# Export results via web interface
# Visit http://localhost:5000 and click "Export Results"
```

### Test different K-factors
```bash
# Lower K = more stable ratings (chess-like)
python -m src.main --matches 500 --k 16

# Higher K = more volatile ratings (fast progression)
python -m src.main --matches 500 --k 48
```

### Enable arcade mode for exciting comebacks
```bash
# 10% bonus per win in streak
python -m src.main --matches 500 --arcade --streak-bonus 0.1
```

---

##  Technologies Used

- **Python 3.12+**: Core simulation engine
- **Flask**: Web framework for API and UI
- **Chart.js**: Interactive rating distribution charts
- **Vanilla JavaScript**: Frontend logic (no heavy frameworks)
- **CSS3**: Modern, responsive design with dark/light themes

---

##  Contributing

Contributions are welcome! Feel free to:
- Report bugs or request features via Issues
- Submit pull requests with improvements
- Share your simulation results

---

##  License

MIT License - see LICENSE file for details

---

##  Screenshots

### Dark Mode
![Dark Mode](https://github.com/user-attachments/assets/3e9e87f1-6c3c-4f50-a961-40dd241dc0ca)

### Light Mode
![Light Mode](https://github.com/user-attachments/assets/9339c7d0-b520-42b5-99c9-f537e4e35741)

### Analytics Dashboard
![Analytics](https://github.com/user-attachments/assets/984919aa-04ff-4d18-97bf-eae5a5a65939)

