# Layer 2 Project Structure

## Current Directory Tree

```
├── layer2_simulation/          # Main project directory
│   └── model/                  # Core SEIRS model
│       ├── __init__.py         # Package exports
│       ├── agent.py            # DisinformationAgent class (SEIRS transitions)
│       ├── archetypes.py       # 5 psychographic profiles & constants
│       ├── model.py            # DisinformationModel class (network, seeding, metrics)
│       └── narrative.py        # Narrative dataclass (β₀, Emo, Idw, p₀)
│
├── test_model.py               # Simple test script (validates model works)
└── PROGRESS.md                 # Development progress tracker
```

## Planned Structure (To Be Built)

```
├── layer2_simulation/
│   ├── model/                  # ✅ COMPLETED
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── archetypes.py
│   │   ├── model.py
│   │   └── narrative.py
│   │
│   ├── visualization/          # 🔲 TO BUILD
│   │   ├── __init__.py
│   │   ├── app.py              # Main Solara application
│   │   └── components/
│   │       ├── __init__.py
│   │       ├── controls.py     # Sliders, buttons, inputs
│   │       ├── network_viz.py  # Network graph visualization
│   │       ├── trajectories.py # State trajectory plots
│   │       └── metrics.py      # Summary statistics display
│   │
│   ├── analysis/               # 🔲 TO BUILD
│   │   ├── __init__.py
│   │   ├── metrics.py          # R₀, peak detection, attack rate
│   │   └── export.py           # CSV/PNG export utilities
│   │
│   └── tests/                  # 🔲 OPTIONAL
│       ├── __init__.py
│       ├── test_agent.py
│       ├── test_model.py
│       └── test_metrics.py
│
├── test_model.py               # ✅ Basic functionality test
├── PROGRESS.md                 # ✅ Progress tracker
├── requirements.txt            # 🔲 TO CREATE
└── README.md                   # 🔲 TO CREATE
```

## File Descriptions

### ✅ Completed Files

#### `model/__init__.py` (85 bytes)
Package initialization, exports main classes and constants.

#### `model/agent.py` (9.8 KB)
**DisinformationAgent class**
- Psychographic traits (NFC, Trust, CB, IA)
- SEIRS state transitions
- Transition probability calculations (α, σ, γ, ω)
- Weighted linear multiplier functions

**Key Methods:**
- `step()`: Calculate next state
- `advance()`: Commit state transition
- `_calculate_alpha()`: S→E exposure susceptibility
- `_calculate_sigma()`: E→I adoption rate
- `_calculate_gamma()`: I→R correction rate
- `_calculate_omega()`: R→S relapse rate

#### `model/archetypes.py` (2.5 KB)
**Constants and utilities**
- `ARCHETYPES`: Dict with 5 psychographic profiles
- `validate_archetype_distribution()`: Ensure proportions sum to 1.0
- `get_archetype_counts()`: Calculate agent counts per archetype
- `STATE_COLORS`: Color mappings for visualization
- `STATE_LABELS`: Human-readable state names

**Archetypes:**
1. Immune (20%): NFC=0.85, Trust=0.80, CB=0.20, IA=0.30
2. Superspreader (15%): NFC=0.15, Trust=0.20, CB=0.85, IA=0.90
3. Moderate (50%): All traits = 0.50
4. Critical Thinker (10%): NFC=0.90, Trust=0.50, CB=0.25, IA=0.35
5. Cynical Contrarian (5%): NFC=0.60, Trust=0.15, CB=0.70, IA=0.75

#### `model/model.py` (11.2 KB)
**DisinformationModel class**
- Network generation (Barabási-Albert scale-free)
- Agent creation with archetype distribution
- Initial seeding (random, hub-targeted, archetype-proportional)
- Simultaneous activation simulation
- Data collection via Mesa DataCollector
- R₀ calculation
- Peak metrics extraction

**Key Methods:**
- `step()`: Run one timestep (simultaneous activation)
- `run(max_steps)`: Execute full simulation
- `calculate_R0()`: Compute basic reproduction number
- `get_peak_metrics()`: Extract max_infected, time_to_peak, attack_rate
- `get_archetype_infection_rates()`: Per-archetype statistics

#### `model/narrative.py` (1.2 KB)
**Narrative dataclass**
- `baseline_transmission` (β₀): Base contagion rate
- `emotional_intensity` (Emo): Emotional amplification
- `identity_weight` (Idw): Identity-relevance
- `initial_seeding` (p₀): Initial infection proportion

**Properties:**
- `effective_transmission`: β₀ × (1 + Emo)
- Input validation (all params ∈ [0, 1])

#### `test_model.py` (1.7 KB)
Simple test demonstrating:
- Model initialization
- R₀ calculation
- Simulation execution
- Metrics extraction

**Example Output:**
```
R₀ = 20.39
Peak: 62% infected at step 14
Attack rate: 68.5%
```

### 🔲 To Be Created

#### `visualization/app.py`
Main Solara application with:
- Parameter sliders (narrative, archetypes, network)
- Simulation controls (run, pause, reset, step)
- Real-time plots (trajectories, network)
- Metrics dashboard
- Advanced settings panel

#### `visualization/components/controls.py`
Reusable UI components:
- Slider with label and value display
- Parameter groups
- Button controls
- Validation indicators

#### `visualization/components/network_viz.py`
Network graph visualization:
- Node coloring (by state or archetype)
- Sample mode (200 nodes) vs. full network
- Interactive zoom/pan
- Legend

#### `visualization/components/trajectories.py`
Time-series plots:
- Main SEIRS curves (S, E, I, R over time)
- Archetype-specific infected counts
- Incidence vs. prevalence dual-axis plot
- Export functionality

#### `visualization/components/metrics.py`
Summary statistics display:
- R₀ prediction with components
- Peak prevalence metrics (max, time, attack rate)
- Archetype infection rates with progress bars
- Real-time updates during simulation

#### `analysis/metrics.py`
Advanced metrics calculations:
- R₀ sensitivity analysis
- Peak detection algorithms
- Attack rate confidence intervals
- Archetype-specific reproduction numbers

#### `analysis/export.py`
Data export utilities:
- CSV export (datacollector results)
- PNG/SVG plot exports
- Summary report generation

#### `requirements.txt`
Dependency list:
```
mesa==3.3.1
solara==1.37.0
networkx==3.2.1
numpy==1.26.0
matplotlib==3.8.0
plotly==5.18.0
pandas==2.1.0
```

#### `README.md`
Project documentation:
- Installation instructions
- Quick start guide
- Model description
- Parameter explanations
- Usage examples

## Dependencies Installed

✅ Core:
- mesa==3.3.1
- networkx (latest)
- numpy (latest)
- matplotlib (latest)
- pandas (latest)

✅ Visualization:
- solara==1.37.0
- plotly (latest)

## Usage

### Running the Test
```bash
cd /home/claude
python test_model.py
```

### Running Solara (once built)
```bash
cd /home/claude/layer2_simulation
solara run visualization/app.py
```

---

**Status:** Phase 1 Complete (Core Model) | Phase 2 Pending (Visualization)
**Next:** Build Solara interface components



# Thesis ABM — Mesa 3.3.1 + Solara Visualization

### Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


