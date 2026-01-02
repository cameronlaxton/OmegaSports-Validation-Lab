# 🎯 START HERE - OmegaSports Validation Lab Navigation Guide

> **New to this repository?** This is your roadmap. Read this first to understand what this project does and how everything fits together.

## 🔍 What Is This Repository?

The **OmegaSports Validation Lab** is a **research and testing platform** for calibrating and validating sports betting models. Think of it as a **scientific laboratory** where you:

1. **Collect historical sports data** (game results, player stats, betting lines)
2. **Test betting strategies** against historical data
3. **Calibrate model parameters** to improve prediction accuracy
4. **Validate improvements** before deploying to production

## 🤝 Relationship to OmegaSports Engine

### Two Separate Repositories - One Purpose

```
┌─────────────────────────────────────┐
│   OmegaSports Engine (Production)   │  ← Makes real-time betting predictions
│   - Live game predictions           │
│   - Monte Carlo simulations         │
│   - Production betting decisions    │
└─────────────────────────────────────┘
                  ↕
         (Research & Calibration)
                  ↕
┌─────────────────────────────────────┐
│  OmegaSports Validation Lab (This)  │  ← Tests & improves the engine
│  - Historical data collection       │
│  - Strategy backtesting             │
│  - Parameter optimization           │
│  - Performance validation           │
└─────────────────────────────────────┘
```

### Why Two Repositories?

**Separation of Concerns:**
- **Production Engine**: Stable, fast, deployed code for live betting
- **Validation Lab**: Experimental, research-focused, constantly evolving

**The Connection:**
1. Lab **tests strategies** using historical data
2. Lab **finds optimal parameters** (edge thresholds, Kelly fractions, etc.)
3. Lab **validates improvements** meet statistical significance
4. **Only then** → Parameters flow back to production engine

**Analogy**: 
- Engine = Factory floor (production)
- Lab = R&D department (research & testing)

You **must link** them because the lab needs to test the same models the engine uses, but you **keep them separate** so experiments don't break production.

## 📚 Documentation Navigation

**Too many docs?** Here's what to read and when:

### 🚀 Getting Started (Read First)
1. **[START_HERE.md](START_HERE.md)** ← You are here
2. **[README.md](README.md)** - Project overview and quick start
3. **[INSTALLATION.md](INSTALLATION.md)** - Setup instructions
4. **[GETTING_STARTED.md](GETTING_STARTED.md)** - Your first experiments

### 🏗️ Architecture & Design (Developers)
5. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and data flow
6. **[DATABASE_STORAGE_GUIDE.md](DATABASE_STORAGE_GUIDE.md)** - How data is stored ⭐ **ADDRESSES YOUR QUESTION**
7. **[DATA_COLLECTION_GUIDE.md](DATA_COLLECTION_GUIDE.md)** - How to collect historical data
8. **[DATA_SOURCE_STRATEGY.md](DATA_SOURCE_STRATEGY.md)** - Data sources explained

### 🔬 Running Experiments
9. **[EXPERIMENTS.md](EXPERIMENTS.md)** - Experiment protocols
10. **[API_USAGE_GUIDE.md](API_USAGE_GUIDE.md)** - Working with data APIs

### 📊 Project Status (Reference)
11. **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current progress
12. **[PHASE_2_QUICKSTART.md](PHASE_2_QUICKSTART.md)** - Daily task reference

### 📋 Archive (Historical - Skip Unless Curious)
- `PHASE_*.md` files - Development phase documentation
- `COMPLETE_STATUS.md`, `IMPLEMENTATION_SUMMARY.md` - Progress snapshots
- `SQLITE_MIGRATION_COMPLETE.md` - Migration details

## ❓ Your Questions Answered

### Q1: "Why link the two repositories?"

**Answer:** For **continuous calibration and improvement**.

The Validation Lab needs to:
1. Use the **same simulation logic** as the production engine
2. Test changes **before** they go live
3. Provide **feedback loop** for parameter tuning

Without linking:
- ❌ Can't validate that lab improvements work in production
- ❌ Have to manually copy parameters (error-prone)
- ❌ No guarantee lab and production stay in sync

With linking:
- ✅ Lab tests using production code
- ✅ Validated parameters automatically deployable
- ✅ Consistent methodology between research and production

### Q2: "How do I store historical data in a database?"

**Answer:** It's already implemented! See [DATABASE_STORAGE_GUIDE.md](DATABASE_STORAGE_GUIDE.md)

**Quick Start:**
```bash
# Collect historical data and store in SQLite database
python scripts/collect_historical_sqlite.py \
    --sports NBA NFL \
    --start-year 2020 \
    --end-year 2024

# Check what's stored
sqlite3 data/sports_data.db "SELECT COUNT(*) FROM games;"
```

**What you get:**
- SQLite database at `data/sports_data.db` (36 MB currently)
- 5 tables: `games`, `player_props`, `odds_history`, `player_props_odds`, `perplexity_cache`
- ~14,000 games stored with statistics and betting lines
- Thread-safe, concurrent access with WAL mode

**See full details:** [DATABASE_STORAGE_GUIDE.md](DATABASE_STORAGE_GUIDE.md)

### Q3: "Too many scripts - which one should I use?"

**Answer:** Use these **core scripts** only:

#### For Data Collection:
```bash
# Modern: SQLite-based (RECOMMENDED)
python scripts/collect_historical_sqlite.py --sports NBA NFL --start-year 2020 --end-year 2024

# Legacy: JSON-based (for compatibility)
python scripts/load_and_validate_games.py --sports NBA NFL
```

#### For Checking Status:
```bash
python scripts/check_status.py
```

#### For Running Experiments:
```bash
python run_all_modules.py
```

**Deprecated/Experimental** (ignore these):
- `bulk_collect.py` - Old batch collection approach
- `collect_games_only.py` - Superseded by collect_historical_sqlite.py
- `collect_historical_5years.py` - Old multi-year collection
- `collect_historical_odds.py` - Now integrated into collect_historical_sqlite.py
- `enrich_*.py` - Experimental enrichment scripts

See section below on "Script Consolidation" for migration plan.

### Q4: "How do I organize data collection code?"

**Answer:** The architecture is already organized:

```
Core Layer (Don't Touch - Stable):
├── core/db_manager.py              ← Database access (SQLite)
├── core/data_pipeline.py           ← Data loading/validation
├── core/historical_data_scraper.py ← ESPN scraping logic
└── core/multi_source_aggregator.py ← Multi-source enrichment

Script Layer (Your Entry Points):
├── scripts/collect_historical_sqlite.py  ← Main collection script
├── scripts/check_status.py               ← Status checker
└── scripts/load_and_validate_games.py    ← Legacy JSON loader

Experiment Layer:
├── run_all_modules.py              ← Run all experiments
└── modules/01_edge_threshold/      ← Individual experiments
```

**Pattern:**
1. **Core** = Reusable library functions
2. **Scripts** = Command-line entry points
3. **Modules** = Experiment implementations

## 🛠️ Quick Start Commands

### 1. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Collect Historical Data
```bash
# Collect and store in database (recommended)
python scripts/collect_historical_sqlite.py \
    --sports NBA NFL \
    --start-year 2022 \
    --end-year 2024 \
    --workers 2
```

### 3. Check What You Have
```bash
# Quick status check
python scripts/check_status.py

# Database inspection
sqlite3 data/sports_data.db "
SELECT sport, COUNT(*) as game_count 
FROM games 
GROUP BY sport;
"
```

### 4. Run Experiments
```bash
# Run Module 1: Edge Threshold Calibration
python run_all_modules.py --module 01

# Run all modules
python run_all_modules.py
```

## 🗺️ File Organization

### What Goes Where

```
OmegaSports-Validation-Lab/
│
├── 📖 START_HERE.md                 ← Read this first (you are here)
├── 📖 README.md                     ← Project overview
│
├── 📁 core/                         ← Core library (stable)
│   ├── db_manager.py                ← Database layer
│   ├── data_pipeline.py             ← Data loading
│   └── *.py                         ← Other core modules
│
├── 📁 scripts/                      ← CLI entry points
│   ├── collect_historical_sqlite.py ← Main data collection
│   ├── check_status.py              ← Status checker
│   └── *.py                         ← Other utilities
│
├── 📁 modules/                      ← Experiments
│   ├── 01_edge_threshold/           ← Module 1
│   └── 02_iteration_optimization/   ← Module 2
│
├── 📁 data/                         ← Data storage
│   ├── sports_data.db               ← SQLite database (36 MB)
│   ├── historical/                  ← Legacy JSON files
│   └── logs/                        ← Log files
│
├── 📁 docs/                         ← Detailed documentation
│   └── (31 markdown files)          ← Reference docs
│
└── 📄 requirements.txt              ← Python dependencies
```

## 🚨 Common Issues & Solutions

### "I can't build a database"
✅ **Solution:** You already have one! See `data/sports_data.db`
- Check size: `ls -lh data/sports_data.db`
- Inspect: `sqlite3 data/sports_data.db ".tables"`
- Use the guide: [DATABASE_STORAGE_GUIDE.md](DATABASE_STORAGE_GUIDE.md)

### "Too many files, don't know which to use"
✅ **Solution:** Use the core scripts (see Q3 above)
- Data collection: `scripts/collect_historical_sqlite.py`
- Status check: `scripts/check_status.py`
- Experiments: `run_all_modules.py`

### "Scripts overlap and conflict"
✅ **Solution:** Script consolidation plan below
- Legacy scripts will be deprecated
- Core functionality consolidated into 3-4 main scripts
- See "Migration & Cleanup Plan" section

### "Don't understand repo relationship"
✅ **Solution:** See Q1 above
- Lab = Research & testing
- Engine = Production deployment
- Link = Parameter flow and validation

## 📋 Migration & Cleanup Plan

### Deprecated Scripts (Will Be Removed)

Moving forward, **ignore these scripts** (they're experimental/obsolete):

```bash
# DEPRECATED - DO NOT USE
scripts/bulk_collect.py              # Use collect_historical_sqlite.py instead
scripts/collect_games_only.py        # Use collect_historical_sqlite.py instead
scripts/collect_historical_5years.py # Use collect_historical_sqlite.py instead
scripts/collect_historical_odds.py   # Now integrated
scripts/enrich_odds.py               # Experimental
scripts/enrich_player_stats.py       # Experimental
```

### Recommended Scripts (Active)

**Use these:**
```bash
# ✅ ACTIVE SCRIPTS
scripts/collect_historical_sqlite.py # Main data collection
scripts/check_status.py              # Status checking
scripts/load_and_validate_games.py   # JSON compatibility layer
scripts/test_api_integration.py      # API testing
```

### Temporary Files to Clean

These should not be in git (already in `.gitignore` but present):
```bash
data/*.pid                  # Process IDs
data/*.log                  # Log files
data/collection*.log        # Collection logs
```

## 📞 Need Help?

### Documentation by Topic

| Topic | Document | Purpose |
|-------|----------|---------|
| **Getting started** | [GETTING_STARTED.md](GETTING_STARTED.md) | First-time setup |
| **Database storage** | [DATABASE_STORAGE_GUIDE.md](DATABASE_STORAGE_GUIDE.md) | How data is stored |
| **Data collection** | [DATA_COLLECTION_GUIDE.md](DATA_COLLECTION_GUIDE.md) | How to collect data |
| **Running experiments** | [EXPERIMENTS.md](EXPERIMENTS.md) | Experiment protocols |
| **Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md) | System design |
| **API usage** | [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md) | Working with APIs |

### Still Stuck?

1. Check [PROJECT_STATUS.md](PROJECT_STATUS.md) for current state
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for design decisions
3. Open an issue with specific questions

## ✅ Next Steps

1. **Read this document** ✓ (You're doing it!)
2. **Install dependencies** → [INSTALLATION.md](INSTALLATION.md)
3. **Collect sample data** → Use `collect_historical_sqlite.py`
4. **Run first experiment** → Use `run_all_modules.py --module 01`
5. **Review results** → Check `data/experiments/`

---

**Last Updated:** January 2, 2026  
**Repository Version:** Phase 2 (Baseline Establishment)  
**Status:** Active Development
