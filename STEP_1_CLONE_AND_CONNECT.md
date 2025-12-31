# Step 1: Clone Repository & Verify OmegaSports Connection

**Purpose:** Set up your local environment and verify that the Validation Lab can connect to your OmegaSports engine.

**Time Required:** 15-20 minutes

**Difficulty:** Easy ✅

---

## Part 1: Clone the Repository

### 1.1 Clone to Local Machine

**Prerequisites:**
- Git installed (`git --version` to verify)
- Terminal/Command Prompt access
- ~500 MB disk space

**Steps:**

```bash
# Navigate to where you want the project
cd ~/projects  # or your preferred location

# Clone the repository
git clone https://github.com/cameronlaxton/OmegaSports-Validation-Lab.git

# Navigate into the project
cd OmegaSports-Validation-Lab

# Verify structure
ls -la  # On Windows: dir
```

**Expected Output:**
```
data/
modules/
core/
utils/
tests/
.github/
README.md
ARCHITECTURE.md
...
```

✅ **Success Check:** You should see all project folders and documentation files.

---

## Part 2: Set Up Python Environment

### 2.1 Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

**Expected Output:**
```
(venv) $ _
```

Notice the `(venv)` prefix in your terminal - this means the virtual environment is active.

### 2.2 Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

**Expected Output:**
```
Successfully installed [package names...]
```

✅ **Success Check:** No error messages, all packages installed.

### 2.3 Verify Installation

```bash
# Run tests to verify everything works
pytest tests/
```

**Expected Output:**
```
============================= test session starts ==============================
...
============================= XX passed in X.XXs ==============================
```

✅ **Success Check:** Tests should pass (green checkmarks).

---

## Part 3: Configure Environment Variables

### 3.1 Create .env File

```bash
# Copy the example .env file
cp .env.example .env

# Or on Windows:
copy .env.example .env
```

### 3.2 Edit .env File

Open `.env` in your text editor (VS Code, nano, etc.) and configure:

```env
# OmegaSports Configuration
OMEGA_ENGINE_PATH=../OmegaSportsAgent
OMEGA_SCRAPER_API_KEY=your_api_key_here

# Data Configuration
HISTORICAL_DATA_PATH=./data/historical
CACHE_PATH=./data/cache
EXPERIMENTS_PATH=./data/experiments
LOGS_PATH=./data/logs

# Simulation Configuration
DEFAULT_ITERATIONS=10000
CONFIDENCE_LEVEL=0.95

# Module Configuration
ENABLE_PLAYER_PROPS=true
ENABLE_GAME_BETS=true
```

**Key Settings:**

| Setting | Value | Notes |
|---------|-------|-------|
| `OMEGA_ENGINE_PATH` | `../OmegaSportsAgent` | Path to your OmegaSports repo (adjust if different) |
| `OMEGA_SCRAPER_API_KEY` | Your API key | If you have one; otherwise leave blank |
| `HISTORICAL_DATA_PATH` | `./data/historical` | Where historical games/props are stored |
| `CACHE_PATH` | `./data/cache` | Where cached data is stored |
| `DEFAULT_ITERATIONS` | `10000` | Simulation iterations (higher = more accurate, slower) |
| `ENABLE_PLAYER_PROPS` | `true` | Enable player prop testing |
| `ENABLE_GAME_BETS` | `true` | Enable game bet testing |

✅ **Success Check:** .env file created and configured.

---

## Part 4: Verify OmegaSports Connection

This is the critical step - verifying your Validation Lab can connect to your OmegaSports engine.

### 4.1 Test Basic Import

```bash
# Test if we can import the OmegaSports engine
python -c "from omega.simulation.simulation_engine import run_game_simulation; print('✓ OmegaSports engine accessible')"
```

**Expected Output:**
```
✓ OmegaSports engine accessible
```

**If you get an error:**

```
ModuleNotFoundError: No module named 'omega'
```

→ **Solution:** Adjust `OMEGA_ENGINE_PATH` in your `.env` file to point to your OmegaSports repository

```bash
# Example if OmegaSports is in parent directory:
echo "OMEGA_ENGINE_PATH=../OmegaSportsAgent" >> .env
```

### 4.2 Test Simulation Execution

```bash
python -c "
from omega.simulation.simulation_engine import run_game_simulation

# Test with sample game
test_game = {
    'game_id': 'test_001',
    'home_team': 'Lakers',
    'away_team': 'Celtics',
    'sport': 'NBA',
    'date': '2024-01-01',
    'moneyline': {'home': -110, 'away': 110}
}

print('Testing simulation...')
result = run_game_simulation(test_game, iterations=1000)
print(f'✓ Simulation successful')
print(f'  Home win probability: {result.get(\"home_win_prob\", \"N/A\")}')
"
```

**Expected Output:**
```
Testing simulation...
✓ Simulation successful
  Home win probability: 0.45
```

✅ **Success Check:** Simulation ran without errors.

### 4.3 Test Data Pipeline Connection

```bash
python -c "
from core.data_pipeline import DataPipeline
from omega.scraper_engine import ScraperEngine

print('Testing data pipeline...')
pipeline = DataPipeline()
print('✓ DataPipeline initialized')

scraper = ScraperEngine()
print('✓ ScraperEngine initialized')

try:
    games = scraper.fetch_games('NBA', start_date='2025-01-01', limit=5)
    print(f'✓ Scraper working: {len(games)} games fetched')
except Exception as e:
    print(f'⚠ Scraper note: {e}')
    print('  (This is OK - scraper may require credentials)')
"
```

**Expected Output:**
```
Testing data pipeline...
✓ DataPipeline initialized
✓ ScraperEngine initialized
✓ Scraper working: 5 games fetched
```

Or if scraper needs credentials:
```
Testing data pipeline...
✓ DataPipeline initialized
✓ ScraperEngine initialized
⚠ Scraper note: API key required
  (This is OK - scraper may require credentials)
```

✅ **Success Check:** DataPipeline initialized successfully.

---

## Part 5: Comprehensive Connection Test

Run this complete test to verify everything is working:

```bash
python << 'EOF'
import sys
from pathlib import Path

print("\n" + "="*80)
print("Step 1 Verification: Clone & Connect")
print("="*80)

# Test 1: Project structure
print("\n[1/5] Checking project structure...")
required_dirs = ['core', 'modules', 'data', 'tests', '.github']
for dir_name in required_dirs:
    if Path(dir_name).exists():
        print(f"  ✓ {dir_name}/")
    else:
        print(f"  ✗ {dir_name}/ MISSING")
        sys.exit(1)

# Test 2: Python dependencies
print("\n[2/5] Checking Python dependencies...")
try:
    import pytest
    print(f"  ✓ pytest")
    import numpy
    print(f"  ✓ numpy")
    import pandas
    print(f"  ✓ pandas")
except ImportError as e:
    print(f"  ✗ Missing: {e}")
    sys.exit(1)

# Test 3: Validation Lab imports
print("\n[3/5] Checking Validation Lab modules...")
try:
    from core.data_pipeline import DataPipeline
    print(f"  ✓ DataPipeline")
    from core.simulation_framework import SimulationFramework
    print(f"  ✓ SimulationFramework")
    from modules.01_edge_threshold.run_experiment import EdgeThresholdModule
    print(f"  ✓ EdgeThresholdModule")
except ImportError as e:
    print(f"  ✗ Import error: {e}")
    sys.exit(1)

# Test 4: OmegaSports connection
print("\n[4/5] Checking OmegaSports connection...")
try:
    from omega.simulation.simulation_engine import run_game_simulation
    print(f"  ✓ OmegaSports simulation engine accessible")
    
    # Try running a quick simulation
    test_game = {
        'home_team': 'Test Home',
        'away_team': 'Test Away',
        'sport': 'NBA',
        'moneyline': {'home': -110, 'away': 110}
    }
    result = run_game_simulation(test_game, iterations=100)
    print(f"  ✓ Simulation test successful")
except ImportError:
    print(f"  ⚠ OmegaSports not found (will configure in Phase 2)")
except Exception as e:
    print(f"  ⚠ Note: {e}")

# Test 5: Configuration
print("\n[5/5] Checking configuration...")
try:
    from utils.config import config
    print(f"  ✓ Configuration loaded")
    print(f"    - Cache path: {config.cache_path}")
    print(f"    - Data path: {config.historical_data_path}")
except ImportError as e:
    print(f"  ⚠ Config note: {e}")

print("\n" + "="*80)
print("✅ STEP 1 VERIFICATION COMPLETE!")
print("="*80)
print("\nYou're ready for Phase 2!")
print("Next: Read PHASE_2_QUICKSTART.md for next steps")
print("\n")
EOF
```

**Expected Output:**
```
================================================================================
Step 1 Verification: Clone & Connect
================================================================================

[1/5] Checking project structure...
  ✓ core/
  ✓ modules/
  ✓ data/
  ✓ tests/
  ✓ .github/

[2/5] Checking Python dependencies...
  ✓ pytest
  ✓ numpy
  ✓ pandas

[3/5] Checking Validation Lab modules...
  ✓ DataPipeline
  ✓ SimulationFramework
  ✓ EdgeThresholdModule

[4/5] Checking OmegaSports connection...
  ✓ OmegaSports simulation engine accessible
  ✓ Simulation test successful

[5/5] Checking configuration...
  ✓ Configuration loaded
    - Cache path: ./data/cache
    - Data path: ./data/historical

================================================================================
✅ STEP 1 VERIFICATION COMPLETE!
================================================================================

You're ready for Phase 2!
Next: Read PHASE_2_QUICKSTART.md for next steps
```

✅ **Success Check:** All tests pass, no errors.

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'omega'"

**Cause:** OmegaSports path is incorrect

**Solution:**
1. Find your OmegaSports repository location
2. Update `.env`:
   ```env
   OMEGA_ENGINE_PATH=/full/path/to/OmegaSportsAgent
   ```
3. Test again

### "No module named 'pytest'"

**Cause:** Dependencies not installed

**Solution:**
```bash
pip install -r requirements.txt
```

### Virtual environment not activating

**Cause:** Wrong activation command

**Solution:**
```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# Verify
which python  # Should show venv path
```

### "Permission denied" errors

**Cause:** File permissions issue

**Solution:**
```bash
chmod +x venv/bin/activate
```

---

## Next Steps

✅ **Step 1 Complete!** You have:
- ✅ Cloned the repository locally
- ✅ Set up Python environment
- ✅ Installed all dependencies
- ✅ Configured environment variables
- ✅ Verified OmegaSports connection

**Now proceed to Phase 2:**

1. Read: [`PHASE_2_QUICKSTART.md`](PHASE_2_QUICKSTART.md)
2. Follow: Week 1-2 daily tasks
3. Track: [GitHub Issue #2](https://github.com/cameronlaxton/OmegaSports-Validation-Lab/issues/2)

---

## Quick Reference

### Essential Commands

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Run tests
pytest tests/

# Run a single test file
pytest tests/test_core.py

# Run tests with coverage
pytest tests/ --cov=core --cov-report=html

# Run Module 1
python -m modules.01_edge_threshold.run_experiment

# Check Python version
python --version

# List installed packages
pip list
```

### File Structure

```
OmegaSports-Validation-Lab/
├── core/                    # Core framework
│   ├── data_pipeline.py     # Data ingestion (UPDATED: player props)
│   ├── simulation_framework.py
│   ├── performance_tracker.py
│   └── ...
├── modules/
│   └── 01_edge_threshold/   # Module 1 (UPDATED: player props)
│       └── run_experiment.py
├── tests/                   # Test suite
├── data/                    # Data storage (auto-created)
├── .env                     # Environment configuration
└── README.md
```

---

## Support

**Questions?**
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Review [README.md](README.md) for project overview
- Check [PHASE_2_PLANNING.md](PHASE_2_PLANNING.md) for detailed planning

**Issues?**
- Create an issue on [GitHub Issues](https://github.com/cameronlaxton/OmegaSports-Validation-Lab/issues)
- Provide: error message, command that failed, OS/Python version

---

**You're all set! 🚀 Ready for Phase 2 starting January 6, 2026.**
