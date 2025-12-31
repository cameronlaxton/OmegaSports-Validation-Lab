# Phase 2 Quick Start Guide

**Start Date:** January 6, 2026  
**Duration:** 4 weeks  
**Status:** Ready to Launch

## 🚀 5-Minute Setup

### 1. Clone Repository (Already done)
```bash
git clone https://github.com/cameronlaxton/OmegaSports-Validation-Lab.git
cd OmegaSports-Validation-Lab
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
python -m pytest tests/
```

You should see: `=== ... passed in X.XXs ===`

---

## ✅ Pre-Phase-2 Verification Checklist

### Before Starting Week 1

- [ ] Clone repository locally
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] All tests passing: `pytest tests/`
- [ ] OmegaSports integration verified:
  ```bash
  python -c "from omega.simulation.simulation_engine import run_game_simulation; print('✓ OmegaSports ready')"
  ```

### Configuration

1. **Create `.env` file:**
```bash
cp .env.example .env
```

2. **Edit `.env` with your settings:**
```env
# OmegaSports Configuration
OMEGA_ENGINE_PATH=../OmegaSportsAgent  # Adjust path to your OmegaSports repo

# Data Configuration
HISTORICAL_DATA_PATH=./data/historical
CACHE_PATH=./data/cache
EXPERIMENTS_PATH=./data/experiments

# Simulation Configuration
DEFAULT_ITERATIONS=10000
CONFIDENCE_LEVEL=0.95
```

3. **Test configuration:**
```bash
python -c "from utils.config import config; print(f'Cache path: {config.cache_path}')"
```

---

## 📈 Week 1-2: Data Pipeline

### What You're Doing
Connecting to your OmegaSports engine and loading historical game data.

### Daily Tasks

**Day 1-2: OmegaSports Integration**
```bash
# Test connection
python -c "
from omega.simulation.simulation_engine import run_game_simulation
from omega.scraper_engine import ScraperEngine

scraper = ScraperEngine()
games = scraper.fetch_games('NBA', start_date='2025-01-01', limit=5)
print(f'✓ Fetched {len(games)} games')
"
```

**Day 3-4: Load Historical Data**
```bash
# Create and run data processing script
python -c "
from core.data_pipeline import DataPipeline

pipeline = DataPipeline()

# Fetch and cache games for all sports
for sport in ['NBA', 'NFL', 'NCAAB', 'NCAAF']:
    games = pipeline.fetch_and_cache_games(sport, 2020, 2024)
    print(f'{sport}: {len(games)} games loaded')
"
```

**Day 5-7: Validate Data**
```bash
# Check data quality
python -c "
from core.data_pipeline import DataPipeline

pipeline = DataPipeline()

for sport in ['NBA', 'NFL', 'NCAAB', 'NCAAF']:
    count = pipeline.get_game_count(sport, 2020, 2024)
    print(f'{sport}: {count} games in database')
    assert count >= 1000, f'{sport} has insufficient data'

print('✓ All sports ready for Module 1')
"
```

### Expected Outputs

```
NBA: 5190 games loaded
NFL: 1280 games loaded
NCAAB: 3450 games loaded
NCAAF: 1320 games loaded

✓ All sports ready for Module 1
```

### Success Criteria
- ✅ 1000+ games per sport
- ✅ Data passes validation
- ✅ Cache working
- ✅ Ready to proceed

---

## 📊 Week 2-3: Baseline Metrics

### What You're Doing
Calculating baseline performance for each sport before optimization.

### Daily Tasks

**Day 8-10: Simulation Integration**
```bash
# Verify simulation framework
python -c "
from core.simulation_framework import SimulationFramework
from core.data_pipeline import DataPipeline

pipeline = DataPipeline()
framework = SimulationFramework()

# Get sample games
games = pipeline.fetch_historical_games('NBA', 2024, 2024)[:5]
print(f'Loaded {len(games)} sample games')

# Run quick simulation
for game in games:
    try:
        result = framework.run_game_simulation(game, iterations=1000)
        print(f'✓ Simulated: {game[\"home_team\"]} vs {game[\"away_team\"]}')
    except Exception as e:
        print(f'Error simulating: {e}')
"
```

**Day 11-14: Calculate Baseline**
```bash
# Calculate baseline metrics
python -c "
from core.data_pipeline import DataPipeline
from core.simulation_framework import SimulationFramework
from core.performance_tracker import PerformanceTracker

pipeline = DataPipeline()
framework = SimulationFramework()
tracker = PerformanceTracker()

print('Calculating baseline metrics...')
for sport in ['NBA', 'NFL', 'NCAAB', 'NCAAF']:
    games = pipeline.fetch_historical_games(sport, 2024, 2024)[:50]
    if games:
        # Simulate batch
        results = []
        for game in games:
            result = framework.run_game_simulation(game, iterations=5000)
            results.append(result)
        
        # Calculate metrics
        metrics = tracker.calculate_metrics(results)
        print(f'{sport}: ROI={metrics.roi:.1%}, Hit Rate={metrics.hit_rate:.1%}')
"
```

### Expected Output
```
Calculating baseline metrics...
NBA: ROI=4.2%, Hit Rate=55.3%
NFL: ROI=3.8%, Hit Rate=54.1%
NCAAB: ROI=4.5%, Hit Rate=55.8%
NCAAF: ROI=3.2%, Hit Rate=53.2%
```

### Success Criteria
- ✅ Simulations running
- ✅ Baseline metrics calculated
- ✅ Documented for all sports

---

## 🧪 Week 3-4: Module 1 Execution

### What You're Doing
Running the first experimental module to find optimal edge thresholds.

### Launch Module 1

**Simple execution:**
```bash
python -m modules.01_edge_threshold.run_experiment
```

**Or with logging:**
```bash
python -c "
import logging
from modules.01_edge_threshold.run_experiment import EdgeThresholdModule

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

module = EdgeThresholdModule()
results = module.run()
print('\n✓ Module 1 execution complete!')
print(f'Results saved to: data/experiments/module_01_results.json')
"
```

### Monitor Progress

**Check logs:**
```bash
tail -f data/logs/experiments.log
```

**View results:**
```bash
python -c "
import json
from pathlib import Path

results_file = Path('data/experiments/module_01_results.json')
if results_file.exists():
    with open(results_file) as f:
        results = json.load(f)
    print(f'Total tests: {results[\"results\"][\"total_analysis\"]}')
    print(f'Best threshold: {results[\"results\"][\"analysis\"][\"overall_best_threshold\"]}%')
"
```

### Expected Output
```
================================================================================
Module 1: Edge Threshold Calibration
================================================================================

Phase 1: Loading historical data...
  NBA: 5190 games loaded
  NFL: 1280 games loaded
  NCAAB: 3450 games loaded
  NCAAF: 1320 games loaded

Phase 2: Testing thresholds...
  [100.0%] Completed 168 threshold tests

Phase 3: Analyzing results...
Overall best threshold: 3.5% (ROI: 8.2%)

================================================================================
Module 1: Results Summary
================================================================================
Total threshold tests: 168
Duration: 3456.2 seconds
Overall best threshold: 3.5%
================================================================================

✓ Module 1 execution complete!
```

### Success Criteria
- ✅ 168 threshold tests completed
- ✅ Best thresholds identified
- ✅ Results saved
- ✅ Phase 2 complete

---

## 🔄 Automation (Built-In)

GitHub Actions automatically:

✅ **Run tests** - Every push, daily at 2 AM UTC  
✅ **Run experiments** - Daily at 3 AM UTC  
✅ **Generate reports** - After each experiment  
✅ **Check code quality** - Every push

**View workflow status:**
```bash
# Open in browser
https://github.com/cameronlaxton/OmegaSports-Validation-Lab/actions
```

---

## 🗐 Key Files & Directories

```
OmegaSports-Validation-Lab/
├─ core/                         # Core framework
├─ modules/01_edge_threshold/     # Module 1 (PHASE 2 FOCUS)
├─ data/
│  ├─ historical/                 # Historical game data
│  ├─ cache/                     # Cached responses
│  ├─ experiments/               # Experiment results
│  └─ logs/                      # Execution logs
├─ PHASE_2_PLANNING.md           # Detailed guide (READ THIS)
├─ ARCHITECTURE.md               # System design
├─ .github/workflows/            # Automation scripts
└─ README.md                     # Project overview
```

---

## 📄 Daily Checklist

### Each Day
- [ ] Check logs: `tail -f data/logs/experiments.log`
- [ ] Verify GitHub Actions: Status page
- [ ] Commit changes: `git add -A && git commit -m "Phase 2 progress"`
- [ ] Push updates: `git push`

### Each Week
- [ ] Review PHASE_2_PLANNING.md progress
- [ ] Update GitHub Issue #2
- [ ] Check test coverage: `pytest --cov`
- [ ] Review data quality

---

## 🙅 Troubleshooting

### "ImportError: No module named omega"

**Solution:** Set OMEGA_ENGINE_PATH in .env:
```bash
echo "OMEGA_ENGINE_PATH=../OmegaSportsAgent" >> .env
```

### "No games found in database"

**Solution:** Run data pipeline first:
```bash
python -c "
from core.data_pipeline import DataPipeline
pipeline = DataPipeline()
for sport in ['NBA', 'NFL', 'NCAAB', 'NCAAF']:
    games = pipeline.fetch_and_cache_games(sport, 2020, 2024)
    pipeline.save_games(games, sport, 2024)
"
```

### "Simulation taking too long"

**Solution:** Reduce iterations or sample size:
```python
# Use fewer iterations for testing
results = framework.run_game_simulation(game, iterations=1000)  # Not 10000

# Or test with sample games
games = games[:10]  # Not all games
```

### "GitHub Actions failing"

**Solution:** Check workflow logs:
1. Go to https://github.com/cameronlaxton/OmegaSports-Validation-Lab/actions
2. Click failed workflow
3. Expand error logs
4. Fix locally and push

---

## 📑 Important Links

- **Phase 2 GitHub Issue:** https://github.com/cameronlaxton/OmegaSports-Validation-Lab/issues/2
- **Phase 2 Detailed Planning:** [PHASE_2_PLANNING.md](PHASE_2_PLANNING.md)
- **Architecture Guide:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Experiment Protocols:** [EXPERIMENTS.md](EXPERIMENTS.md)
- **GitHub Actions:** https://github.com/cameronlaxton/OmegaSports-Validation-Lab/actions

---

## 🎬 Support

**Need help?**

1. Check [PHASE_2_PLANNING.md](PHASE_2_PLANNING.md) for detailed explanations
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
3. Check GitHub Issue #2 for progress updates
4. Review logs in `data/logs/`

---

## ✅ Ready?

**Phase 2 starts January 6, 2026!**

🚀 **Let's go!**

```bash
# Quick start command
python -m modules.01_edge_threshold.run_experiment
```
