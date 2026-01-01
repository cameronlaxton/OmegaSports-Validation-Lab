# OmegaSports Validation Lab - AI Coding Agent Instructions

## Project Purpose

This is an **experimental research framework** for validating and optimizing sports betting algorithms. It tests the OmegaSports betting engine through systematic experimentation with Monte Carlo simulations, statistical validation, and parameter optimization across multiple sports (NBA, NFL, NCAAB, NCAAF).

**Key Distinction**: This is NOT the production betting engine. It's a companion research platform that feeds validated optimizations back to the OmegaAgent production system.

## Architecture Overview

### Three-Layer System
1. **Data Pipeline Layer** ([core/data_pipeline.py](../core/data_pipeline.py))
   - Ingests from ESPN API (scoreboard endpoint, NOT scheduler)
   - Validates real game data vs mocked/sample data (strict validation)
   - Supports both game-level bets (moneyline/spread/total) AND player props
   - Intelligent caching (24-hour expiry) to minimize API calls
   
2. **Simulation Framework Layer** ([core/simulation_framework.py](../core/simulation_framework.py))
   - Unified interface via `ExperimentConfig` dataclass
   - Integrates with OmegaSports Monte Carlo + Markov Chain engines
   - **Monte Carlo Simulations**: Used for game outcome predictions
     - Random sampling from team performance distributions
     - Handles variance in scoring, turnovers, shooting percentages
     - Typical iterations: 10,000 (configurable in Module 2)
     - Best for: Point spreads, totals, final score distributions
   - **Markov Chain Simulations**: Used for possession-level modeling
     - State transitions (possession → scoring/turnover/defensive stop)
     - Team-specific transition probabilities from historical data
     - Accounts for game flow dynamics and momentum shifts
     - Best for: Player props, in-game probabilities, live betting
   - **Hybrid Approach**: Combine both for comprehensive modeling
     - Monte Carlo for macro-level game outcomes
     - Markov chains for micro-level event probabilities
     - Example: Use Markov for possessions, Monte Carlo for variance
   - Returns structured results with metrics
   
3. **Analysis Layer** ([core/performance_tracker.py](../core/performance_tracker.py), [core/statistical_validation.py](../core/statistical_validation.py))
   - Calculates ROI, hit rate, max drawdown, profit factor
   - Bootstrap confidence intervals and effect sizes
   - Experiment logging with structured JSON output

### Module System
Experiments are self-contained in `modules/XX_name/`:
- Each has `run_experiment.py`, `config.py`, `analysis.py`
- Module 1 (Edge Threshold) tests 14 thresholds × 4 sports × 6 bet types = 336 scenarios
- Modules log to `data/experiments/` with timestamps

## Critical Patterns

### 1. Data Validation is Non-Negotiable
Always validate data to prevent sample/mocked games from corrupting experiments:
```python
# In DataValidator class
- Game IDs must NOT contain: "sample", "test", "mock", "fake"
- Scores must be realistic (not 0-0 for final games)
- Dates must be valid (2000-2026 range)
- Team names must be real (not "TBD" or placeholders)
```

### 2. Experiment Execution Pattern
All modules follow this 5-phase structure:
```python
def run(self) -> Dict[str, Any]:
    self.logger.start_experiment("module_name")
    # Phase 1: Load baseline data
    # Phase 2: Run test scenarios
    # Phase 3: Analyze results
    # Phase 4: Statistical validation
    # Phase 5: Generate report
    return results_dict
```

### 3. Configuration Management
- Global config via `utils.config.config` singleton
- NEVER hardcode paths - use `config.historical_data_path`, `config.experiments_path`, etc.
- Environment variables override defaults (see `.env` file)
- OmegaSports engine path configured via `OMEGA_ENGINE_PATH` env var

### 4. Multi-Sport Support
Sports are UPPERCASE constants: `["NBA", "NFL", "NCAAB", "NCAAF"]`
- Basketball props: `["points", "rebounds", "assists"]`
- Football props: `["passing_yards", "rushing_yards", "touchdowns"]`

### 5. Logging Standards
```python
logger = logging.getLogger(__name__)  # Module-level logger
logger.info(...)  # For workflow milestones
logger.warning(...)  # For recoverable issues
logger.error(...)  # For failures
```

## Developer Workflows

### Running Experiments
```bash
# Individual module
python modules/01_edge_threshold/run_experiment.py

# All modules (framework)
python run_all_modules.py

# With data validation
python scripts/load_and_validate_games.py
```

### Testing
```bash
# Run all tests
pytest tests/ -q

# With coverage
pytest tests/ --cov=core --cov=modules

# Run step verification
python test_step1_verification.py
```

### Data Management
- Historical data: `data/historical/sample_nba_2024_games.json` (example format)
- Experiment results: `data/experiments/module_XX_TIMESTAMP.json`
- Logs: `data/logs/YYYYMMDD.log`
- Cache: Auto-managed by DataPipeline (24h TTL)

### Integration with OmegaSports Engine
The scraper at [omega/scraper_engine.py](../omega/scraper_engine.py) wraps the external OmegaAgent:
```python
from omega.scraper_engine import ScraperEngine
scraper = ScraperEngine()
games = scraper.fetch_games('NBA', start_date='2024-01-01')
```
If OmegaAgent is unavailable, fallback to ESPN API direct calls.

## Key Files Reference

- [ARCHITECTURE.md](../ARCHITECTURE.md) - System design and data flows
- [PHASE_2_PLANNING.md](../PHASE_2_PLANNING.md) - Current implementation timeline and tasks
- [DATA_SOURCE_STRATEGY.md](../DATA_SOURCE_STRATEGY.md) - Multi-source data approach
- [PROJECT_STATUS.md](../PROJECT_STATUS.md) - Phase completion status
- [requirements.txt](../requirements.txt) - Dependencies (pandas, numpy, scipy, pytest, jupyter)

## Common Gotchas

1. **Path Management**: Always use absolute paths from `config` object, not relative paths
2. **Data Validation**: Run `DataValidator.validate_game_data()` on ALL external data before use
3. **Module Results**: Return structured dicts, not printed output - ExperimentLogger handles persistence
4. **Sport Codes**: Use uppercase ("NBA"), not lowercase or mixed case
5. **Player Props vs Game Bets**: Different validation rules - props need `prop_type`, games need `moneyline/spread/total`
6. **Caching**: DataPipeline auto-caches - don't implement duplicate caching in modules
7. **Statistical Significance**: Always include p-values and confidence intervals in reports (see StatisticalValidator)

## Testing Philosophy

- Test with **real data samples**, never mocked fixtures
- All core modules have 100% passing tests (8/8 in [tests/test_core.py](../tests/test_core.py))
- Edge case handling: zero division, empty lists, missing fields
- Type hints enforced throughout codebase

## Planned Experimental Modules

### Module 1: Edge Threshold Calibration ✅
**Status:** Implemented (336 test scenarios)  
Tests edge thresholds (1%-10%) to determine optimal filtering for bets across sports and bet types. Measures ROI, hit rate, and max drawdown at each threshold level.

### Module 2: Simulation Iteration Optimization 🔄
**Status:** In Development  
Determines minimum iterations needed for stable probability estimates vs. computational cost. Tests 1K, 2.5K, 5K, 10K, 25K, 50K iterations and measures convergence rate using Hellinger distance.

### Module 3: Variance Scalar Tuning 📝
**Status:** Planned  
Calibrates variance parameters to match real-world outcome distributions. Uses Kolmogorov-Smirnov tests to ensure simulated score distributions align with historical data by sport and game context.

### Module 4: Kelly Criterion Validation 📝
**Status:** Planned  
Tests full Kelly, fractional Kelly (1/2, 1/4, 1/8), and alternative staking methods. Measures compound annual growth rate, maximum drawdown, and probability of ruin across different bankroll management strategies.

### Module 5: Model Combination Testing 📝
**Status:** Planned  
Explores ensemble methods combining multiple predictive models. Tests weighted averaging, stacking, and blending approaches. Measures whether ensemble accuracy exceeds individual model performance.

### Module 6: Injury Impact Quantification 📝
**Status:** Planned  
Develops systematic framework for quantifying player injury impacts. Creates position-specific adjustment factors based on historical injury data. Tests accuracy improvement when incorporating injury adjustments.

### Module 7: Market Efficiency Analysis 📝
**Status:** Planned  
Investigates market inefficiencies to identify optimal betting opportunities. Analyzes closing line value (CLV), market timing patterns, and segment efficiency across different sports, bet types, and game contexts.

### Module 8: Backtesting Framework 📝
**Status:** Planned  
Implements rigorous backtesting with proper train-test separation and walk-forward analysis. Validates all findings from Modules 1-7 on out-of-sample data to ensure production readiness.

## Current State (Phase 1 Complete)

✅ Core infrastructure operational (DataPipeline, SimulationFramework, PerformanceTracker, ExperimentLogger, StatisticalValidator)  
✅ Module 1 (Edge Threshold) fully implemented with 336 test scenarios  
✅ Multi-sport support (4 sports) and player props integrated  
🔄 Phase 2 starting: OmegaAgent integration and baseline establishment  
🔄 Module 2 in development, Modules 3-8 planned with specifications ready

## Simulation Strategy Guidelines

**When to use Monte Carlo:**
- Predicting final game outcomes (spreads, totals, moneylines)
- Modeling score distributions with known variance
- Large-sample aggregations (e.g., season-long projections)
- When computational speed is acceptable (10K+ iterations)

**When to use Markov Chains:**
- Modeling possession-by-possession game flow
- Player prop predictions (points, rebounds, assists)
- Live betting with dynamic state transitions
- When game context matters (score, time, momentum)

**When to use Hybrid:**
- Comprehensive game modeling that needs both macro outcomes and micro events
- Validation studies comparing different simulation approaches
- Player props that depend on total game scoring (e.g., player points over/under in high/low scoring games)

When making changes, preserve the modular experiment structure and statistical rigor that defines this lab's approach.
