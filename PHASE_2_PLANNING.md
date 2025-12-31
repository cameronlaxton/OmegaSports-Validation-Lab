# Phase 2: Baseline Establishment & Module 1 Execution

**Timeline:** January 6 - February 2, 2026 (4 weeks)  
**Status:** Ready to Start  
**Last Updated:** December 31, 2025

## Executive Summary

Phase 2 focuses on establishing baseline performance metrics for your betting engine and executing the first experimental module. This phase will:

1. **Connect infrastructure** to OmegaSports engine
2. **Process historical data** from 2020-2024 across all sports
3. **Calculate baseline metrics** to establish performance foundation
4. **Execute Module 1** - Edge Threshold Calibration
5. **Validate findings** statistically and generate actionable recommendations

By the end of Phase 2, you'll have:
- ✅ Fully functional data pipeline
- ✅ 1000+ games per sport processed
- ✅ Baseline performance metrics documented
- ✅ Optimal edge thresholds identified for all sports/bet types
- ✅ Statistically validated recommendations

---

## Phase 2 Timeline

```
Week 1-2: Data Pipeline Implementation
├─ Connect to OmegaSports engine
├─ Process historical data (2020-2024)
├─ Set up caching and validation
└─ Ready for Module 1 testing

Week 2-3: Simulation Framework Integration & Baseline Metrics
├─ Integrate with Monte Carlo engine
├─ Calculate baseline performance
├─ Document baseline findings
└─ Ready for threshold testing

Week 3-4: Module 1 Execution
├─ Run 168 threshold tests (14 × 4 × 3)
├─ Analyze results statistically
├─ Generate comprehensive report
└─ Complete Phase 2
```

---

## Week 1-2: Data Pipeline Implementation

### 🎯 Objectives

- [ ] Verify OmegaSports integration
- [ ] Implement data fetching for all 4 sports
- [ ] Process 2020-2024 historical data
- [ ] Set up intelligent caching
- [ ] Validate data quality
- [ ] Create sample datasets

### 📋 Detailed Tasks

#### Task 1.1: OmegaSports Integration Test (2-3 hours)

**What:** Verify that your OmegaSports engine is accessible and working

**Steps:**
```bash
# 1. Verify OmegaSports import
python -c "from omega.simulation.simulation_engine import run_game_simulation; print('✓ OmegaSports accessible')"

# 2. Test simulation
python -c "
import json
from omega.simulation.simulation_engine import run_game_simulation

# Test with sample game
test_game = {
    'home_team': 'Lakers',
    'away_team': 'Celtics',
    'sport': 'NBA',
    'moneyline': {'home': -110, 'away': 110}
}

result = run_game_simulation(test_game, iterations=1000)
print(f'✓ Simulation test passed: {result}')
"

# 3. Verify data output format
python -c "
from omega.scraper_engine import ScraperEngine

scraper = ScraperEngine()
games = scraper.fetch_games('NBA', start_date='2025-01-01', limit=5)
print(f'✓ Scraper test passed: {len(games)} games fetched')
"
```

**Expected Output:**
```
✓ OmegaSports accessible
✓ Simulation test passed: {...}
✓ Scraper test passed: 5 games fetched
```

**Acceptance Criteria:**
- ✅ Can import OmegaSports modules
- ✅ Can run simulation on test game
- ✅ Can fetch games from scraper
- ✅ Data format matches expectations

#### Task 1.2: Implement Data Fetching (3-4 hours)

**What:** Extend DataPipeline to fetch from OmegaSports scraper

**Implementation:**
```python
# In core/data_pipeline.py, add to DataPipeline class:

def fetch_from_omega_engine(self, sport: str, season: int) -> List[Dict[str, Any]]:
    """
    Fetch games from OmegaSports scraper engine.
    
    Args:
        sport: Sport name (NBA, NFL, etc.)
        season: Season year
    
    Returns:
        List of game dictionaries
    """
    from omega.scraper_engine import ScraperEngine
    
    scraper = ScraperEngine()
    
    # Fetch games for season
    games = scraper.fetch_season_games(sport, season)
    
    # Validate each game
    valid_games = []
    for game in games:
        is_valid, error = self.validate_game_data(game)
        if is_valid:
            valid_games.append(game)
        else:
            logger.warning(f"Invalid game: {error}")
    
    return valid_games

def fetch_and_cache_games(self, sport: str, start_year: int, end_year: int) -> List[Dict[str, Any]]:
    """
    Fetch games from OmegaSports and cache them.
    """
    all_games = []
    
    for year in range(start_year, end_year + 1):
        # Check cache first
        cache_key = f"omega_games_{sport}_{year}"
        cached = self.get_cached_data(cache_key)
        
        if cached:
            logger.info(f"Using cached data for {sport} {year}")
            all_games.extend(cached)
        else:
            logger.info(f"Fetching fresh data for {sport} {year}")
            games = self.fetch_from_omega_engine(sport, year)
            self.cache_data(cache_key, games)
            all_games.extend(games)
    
    return all_games
```

**Testing:**
```python
# Test the implementation
from core.data_pipeline import DataPipeline

pipeline = DataPipeline()

# Fetch and cache games
for sport in ['NBA', 'NFL', 'NCAAB', 'NCAAF']:
    games = pipeline.fetch_and_cache_games(sport, 2020, 2024)
    print(f"{sport}: {len(games)} games")
    assert len(games) >= 1000, f"{sport} insufficient data"
```

**Acceptance Criteria:**
- ✅ Fetches games from OmegaSports for all sports
- ✅ Caches results properly
- ✅ Validates game data
- ✅ 1000+ games per sport

#### Task 1.3: Process Historical Data (4-5 hours)

**What:** Load and organize historical data by sport and year

**Implementation:**
```python
# Create process_historical_data.py script

from pathlib import Path
from core.data_pipeline import DataPipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_all_sports():
    """
    Process historical data for all sports.
    """
    pipeline = DataPipeline()
    sports = ['NBA', 'NFL', 'NCAAB', 'NCAAF']
    
    for sport in sports:
        logger.info(f"\nProcessing {sport}...")
        
        # Fetch from OmegaSports
        games = pipeline.fetch_and_cache_games(sport, 2020, 2024)
        
        # Save by year
        for year in range(2020, 2025):
            year_games = [g for g in games if g['date'].startswith(str(year))]
            if year_games:
                saved = pipeline.save_games(year_games, sport, year)
                logger.info(f"  {year}: {saved} games saved")
        
        # Summary
        total = pipeline.get_game_count(sport, 2020, 2024)
        logger.info(f"  Total {sport}: {total} games")

if __name__ == "__main__":
    process_all_sports()
    print("\n✓ Historical data processing complete!")
```

**Running:**
```bash
python process_historical_data.py
```

**Expected Output:**
```
Processing NBA...
  2020: 1030 games saved
  2021: 1080 games saved
  2022: 1100 games saved
  2023: 1030 games saved
  2024: 950 games saved
  Total NBA: 5190 games

Processing NFL...
  2020: 256 games saved
  ...
  Total NFL: 1280 games

✓ Historical data processing complete!
```

**Acceptance Criteria:**
- ✅ All sports processed
- ✅ Data organized by year
- ✅ 1000+ games per sport
- ✅ Files saved to `data/historical/`

#### Task 1.4: Data Quality Validation (2-3 hours)

**What:** Verify data integrity and completeness

**Implementation:**
```python
# Create data_quality_report.py

def validate_historical_data():
    """
    Generate data quality report.
    """
    pipeline = DataPipeline()
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'sports': {}
    }
    
    for sport in ['NBA', 'NFL', 'NCAAB', 'NCAAF']:
        games = pipeline.fetch_historical_games(sport, 2020, 2024)
        
        # Check completeness
        has_scores = sum(1 for g in games if g.get('home_score'))
        has_odds = sum(1 for g in games if g.get('moneyline'))
        
        report['sports'][sport] = {
            'total_games': len(games),
            'games_with_scores': has_scores,
            'games_with_odds': has_odds,
            'completeness_pct': (has_scores / len(games) * 100) if games else 0
        }
        
        logger.info(f"{sport}: {len(games)} games, {has_scores} with scores, {has_odds} with odds")
    
    return report

if __name__ == "__main__":
    report = validate_historical_data()
    print(json.dumps(report, indent=2))
```

**Acceptance Criteria:**
- ✅ Data completeness > 95%
- ✅ No corrupted records
- ✅ Date ranges correct
- ✅ Report generated and saved

### 📊 Week 1-2 Deliverables

✅ **Code:**
- [x] DataPipeline implementation (complete)
- [ ] OmegaSports integration tests
- [ ] Historical data processing script
- [ ] Data quality validation script

✅ **Data:**
- [ ] Historical games saved (2020-2024)
- [ ] Cache populated
- [ ] Sample datasets created

✅ **Documentation:**
- [ ] Integration guide
- [ ] Data quality report
- [ ] Ready for Week 2-3

---

## Week 2-3: Simulation Framework Integration & Baseline Metrics

### 🎯 Objectives

- [ ] Connect SimulationFramework to OmegaSports Monte Carlo engine
- [ ] Implement batch simulation processing
- [ ] Calculate baseline metrics for each sport
- [ ] Document baseline findings

### 📋 Detailed Tasks

#### Task 2.1: Simulate Framework Integration (3-4 hours)

**What:** Connect your simulation runner to OmegaSports engine

```python
# Update simulation_framework.py

def run_game_simulation(self, game: Dict[str, Any], iterations: int = 10000) -> Dict[str, Any]:
    """
    Run simulation for single game.
    """
    from omega.simulation.simulation_engine import run_game_simulation as omega_sim
    
    logger.info(f"Running {iterations} simulations for {game['home_team']} vs {game['away_team']}")
    
    # Run through OmegaSports
    results = omega_sim(game, iterations=iterations)
    
    # Parse results
    return {
        'game_id': game.get('game_id'),
        'home_win_prob': results.get('home_win_prob'),
        'away_win_prob': results.get('away_win_prob'),
        'spread_distribution': results.get('spread_distribution'),
        'iterations': iterations
    }

def batch_simulate_games(self, games: List[Dict[str, Any]], iterations: int = 10000) -> List[Dict[str, Any]]:
    """
    Simulate multiple games.
    """
    results = []
    for i, game in enumerate(games):
        logger.info(f"Simulating game {i+1}/{len(games)}")
        result = self.run_game_simulation(game, iterations)
        results.append(result)
    return results
```

#### Task 2.2: Calculate Baseline Metrics (4-5 hours)

**What:** Establish baseline performance for each sport

```python
def calculate_baseline_metrics():
    """
    Calculate baseline metrics for all sports.
    """
    pipeline = DataPipeline()
    framework = SimulationFramework()
    tracker = PerformanceTracker()
    
    baseline = {}
    
    for sport in ['NBA', 'NFL', 'NCAAB', 'NCAAF']:
        logger.info(f"\nCalculating baseline for {sport}...")
        
        # Get games
        games = pipeline.fetch_historical_games(sport, 2020, 2024)
        sample = games[:100]  # Use 100 games for baseline
        
        # Simulate
        sim_results = framework.batch_simulate_games(sample)
        
        # Calculate metrics
        metrics = tracker.calculate_metrics(sim_results)
        
        baseline[sport] = {
            'sample_size': len(sample),
            'hit_rate': metrics['hit_rate'],
            'roi': metrics['roi'],
            'max_drawdown': metrics['max_drawdown'],
            'avg_odds': metrics['avg_odds']
        }
        
        logger.info(f"  Hit Rate: {metrics['hit_rate']:.1%}")
        logger.info(f"  ROI: {metrics['roi']:.1%}")
        logger.info(f"  Max Drawdown: {metrics['max_drawdown']:.1%}")
    
    return baseline
```

**Acceptance Criteria:**
- ✅ Baseline metrics for all 4 sports
- ✅ Metrics saved to `data/experiments/baseline_metrics.json`
- ✅ Report generated and documented

### 📊 Week 2-3 Deliverables

- [ ] SimulationFramework fully integrated
- [ ] Batch processing pipeline
- [ ] Baseline metrics calculated
- [ ] Baseline report generated

---

## Week 3-4: Module 1 Execution

### 🎯 Objectives

- [ ] Execute Module 1: Edge Threshold Calibration
- [ ] Test 14 thresholds × 4 sports × 3 bet types = 168 scenarios
- [ ] Statistically validate all findings
- [ ] Generate comprehensive final report

### 📋 Module 1 Execution

**What:** Run complete threshold calibration

```bash
# Run Module 1
python -m modules.01_edge_threshold.run_experiment
```

**Expected Output:**
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
  [ 10.7%] Testing NBA moneyline @ 1.0% threshold
  [ 11.3%] Testing NBA moneyline @ 1.5% threshold
  ...
  [100.0%] Completed 168 threshold tests

Phase 3: Analyzing results...
Overall best threshold: 3.5% (ROI: 8.2%)

  NBA best: 3.5% threshold (ROI: 8.5%)
  NFL best: 4.0% threshold (ROI: 7.8%)
  NCAAB best: 3.0% threshold (ROI: 8.9%)
  NCAAF best: 4.0% threshold (ROI: 7.2%)

Phase 4: Validating findings...
Phase 5: Generating report...
Report saved to: data/experiments/module_01_results.json

================================================================================
Module 1: Results Summary
================================================================================
Total threshold tests: 168
Duration: 3456.2 seconds
Overall best threshold: 3.5%
================================================================================
```

**Acceptance Criteria:**
- ✅ All 168 tests completed
- ✅ Results statistically validated
- ✅ Best thresholds identified
- ✅ Report generated

### 📊 Week 3-4 Deliverables

- [ ] Module 1 execution complete
- [ ] 168 threshold tests run
- [ ] Results statistically validated
- [ ] Final report generated
- [ ] Recommendations documented

---

## Success Criteria - Phase 2

### 📈 Data Pipeline
- ✅ 1000+ games per sport loaded
- ✅ Data validation pass rate > 95%
- ✅ Caching working properly
- ✅ Historical data saved and organized

### 📊 Baseline Metrics
- ✅ Baseline calculated for all sports
- ✅ Metrics documented
- ✅ Ready for Module 1 comparison

### 🧪 Module 1 Results
- ✅ 168 threshold tests executed
- ✅ Optimal thresholds identified (p < 0.05)
- ✅ ROI improvements vs. baseline significant
- ✅ Confidence intervals calculated

### 💻 Code Quality
- ✅ All tests passing (pytest)
- ✅ No linting errors (flake8)
- ✅ Type checking passing (mypy)
- ✅ Code coverage > 80%

---

## Daily Automation

GitHub Actions workflows handle:

✅ **Daily Test Runs** (`.github/workflows/tests.yml`)
- Runs on schedule and every push
- Tests across Python 3.10, 3.11, 3.12
- Code quality checks

✅ **Daily Experiments** (`.github/workflows/daily-experiments.yml`)
- Runs daily at 3 AM UTC
- Executes all modules
- Archives results

✅ **Report Generation** (`.github/workflows/report-generation.yml`)
- Generates daily reports
- Archives in `reports/` directory
- Commits to repo

✅ **Code Quality** (`.github/workflows/code-quality.yml`)
- Black formatting check
- Import ordering (isort)
- Linting (flake8)
- Type checking (mypy)

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| OmegaSports integration delays | Medium | High | Mock data fallback, parallel development |
| Insufficient historical data | Low | High | Data quality checks, sample datasets |
| Simulation performance issues | Medium | Medium | Batch optimization, caching |
| Statistical anomalies | Low | Medium | Triple validation, peer review |
| Environment setup issues | Low | Medium | Comprehensive docs, Docker support |

---

## Support & Resources

📚 **Documentation:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [INSTALLATION.md](INSTALLATION.md) - Setup guide
- [EXPERIMENTS.md](EXPERIMENTS.md) - Experiment protocols

🐙 **GitHub:**
- [Phase 2 Issue](https://github.com/cameronlaxton/OmegaSports-Validation-Lab/issues/2) - Track progress
- [Pull Requests](https://github.com/cameronlaxton/OmegaSports-Validation-Lab/pulls) - View changes

💬 **Questions?**

Refer to the issue tracker or documentation for guidance.

---

## Next: Phase 3 Preview

After Phase 2 completes, Phase 3 (Weeks 5-8) will focus on:

- **Module 2:** Iteration Optimization
- **Module 3:** Variance Tuning  
- **Module 4:** Kelly Criterion
- **Advanced analysis and optimization**

---

**Ready to begin Phase 2? 🚀**

Verify OmegaSports integration and start Week 1 tasks!
