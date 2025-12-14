"""
Layer 2 SEIRS Disinformation Spread Model - Full Solara Interface

Features:
- Complete parameter controls (narrative, archetypes, network)
- Real-time simulation with play/pause
- State trajectory plots
- Network visualization
- Metrics dashboard
- R₀ calculation
- Advanced settings
"""

import solara
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add model to path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from model.model import DisinformationModel
from model.archetypes import ARCHETYPES, STATE_COLORS


# ============================================================================
# REACTIVE STATE MANAGEMENT
# ============================================================================

# Narrative parameters
narrative_params = solara.reactive({
    'baseline_transmission': 0.45,
    'emotional_intensity': 0.70,
    'identity_weight': 0.75,
    'initial_seeding': 0.06
})

# Archetype distribution
archetype_dist = solara.reactive({
    'immune': 0.20,
    'superspreader': 0.15,
    'moderate': 0.50,
    'critical_thinker': 0.10,
    'cynical_contrarian': 0.05
})

# Population & Network
population_size = solara.reactive(1000)
m_edges = solara.reactive(3)
seeding_strategy = solara.reactive('random')

# Advanced settings
sigma_base = solara.reactive(0.30)
gamma_base = solara.reactive(0.05)
omega_base = solara.reactive(0.02)

# Simulation state
model_instance = solara.reactive(None)
is_running = solara.reactive(False)
current_step = solara.reactive(0)
max_steps = solara.reactive(100)
random_seed = solara.reactive(42)

# UI state
show_advanced = solara.reactive(False)


# ============================================================================
# MAIN PAGE COMPONENT
# ============================================================================

@solara.component
def Page():
    """Main application page with full interface"""
    
    solara.Title("SEIRS Disinformation Spread Model - Layer 2: Baseline Simulation")
    
    with solara.Column(style={"padding": "20px", "max-width": "1400px", "margin": "0 auto"}):
        
        # Header
        with solara.Card(style={"background": "#f0f4f8", "margin-bottom": "20px"}):
            solara.Markdown("""
# SEIRS Disinformation Spread Model
## Layer 2: Baseline Simulation (No Interventions)

*Bachelor's Thesis: Anticipatory Counternarratives Framework*
            """)
        
        # Main content in 2-column layout
        with solara.Columns([2, 3]):
            # Left column: Controls
            with solara.Column():
                NarrativeControls()
                PopulationControls()
                ArchetypeControls()
                SimulationControls()
                
                if show_advanced.value:
                    AdvancedSettings()
            
            # Right column: Visualization & Metrics
            with solara.Column():
                if model_instance.value is not None:
                    R0Display()
                    
                    if current_step.value > 0:
                        TrajectoryPlot()
                        MetricsSummary()


# ============================================================================
# CONTROL COMPONENTS
# ============================================================================

@solara.component
def NarrativeControls():
    """Narrative parameter sliders"""
    with solara.Card("📊 Narrative Parameters", style={"margin-bottom": "15px"}):
        with solara.Column():
            # Baseline Transmission
            solara.Markdown("**Baseline Transmission (β₀)**")
            solara.SliderFloat(
                label="",
                value=narrative_params.value['baseline_transmission'],
                min=0.0,
                max=1.0,
                step=0.01,
                on_value=lambda v: narrative_params.set({**narrative_params.value, 'baseline_transmission': v})
            )
            solara.Markdown(f"*Current: {narrative_params.value['baseline_transmission']:.2f} - Base contagion rate per contact*")
            
            # Emotional Intensity
            solara.Markdown("**Emotional Intensity (Emo)**")
            solara.SliderFloat(
                label="",
                value=narrative_params.value['emotional_intensity'],
                min=0.0,
                max=1.0,
                step=0.01,
                on_value=lambda v: narrative_params.set({**narrative_params.value, 'emotional_intensity': v})
            )
            solara.Markdown(f"*Current: {narrative_params.value['emotional_intensity']:.2f} - Fear, anger, outrage (amplifies transmission)*")
            
            # Identity Weight
            solara.Markdown("**Identity Weight (Idw)**")
            solara.SliderFloat(
                label="",
                value=narrative_params.value['identity_weight'],
                min=0.0,
                max=1.0,
                step=0.01,
                on_value=lambda v: narrative_params.set({**narrative_params.value, 'identity_weight': v})
            )
            solara.Markdown(f"*Current: {narrative_params.value['identity_weight']:.2f} - Identity-relevance (resists correction)*")
            
            # Initial Seeding
            solara.Markdown("**Initial Seeding (p₀)**")
            solara.SliderFloat(
                label="",
                value=narrative_params.value['initial_seeding'],
                min=0.01,
                max=0.20,
                step=0.01,
                on_value=lambda v: narrative_params.set({**narrative_params.value, 'initial_seeding': v})
            )
            n_seeded = int(narrative_params.value['initial_seeding'] * population_size.value)
            solara.Markdown(f"*Current: {narrative_params.value['initial_seeding']:.2f} ({n_seeded} agents start infected)*")


@solara.component
def PopulationControls():
    """Population and network settings"""
    with solara.Card("👥 Population & Network", style={"margin-bottom": "15px"}):
        with solara.Column():
            # Population Size
            solara.Markdown("**Population Size**")
            solara.SliderInt(
                label="",
                value=population_size.value,
                min=100,
                max=5000,
                step=100,
                on_value=population_size.set
            )
            solara.Markdown(f"*Current: {population_size.value} agents*")
            
            # Network Edges
            solara.Markdown("**Network Edges per Node (m)**")
            solara.SliderInt(
                label="",
                value=m_edges.value,
                min=2,
                max=10,
                step=1,
                on_value=m_edges.set
            )
            solara.Markdown(f"*Current: {m_edges.value} connections (Scale-free Barabási-Albert)*")
            
            # Seeding Strategy
            solara.Markdown("**Initial Seeding Strategy**")
            solara.ToggleButtonsSingle(
                value=seeding_strategy.value,
                values=['random', 'hub_targeted', 'archetype_proportional'],
                on_value=seeding_strategy.set
            )


@solara.component
def ArchetypeControls():
    """Archetype distribution sliders"""
    with solara.Card("🧠 Archetype Distribution", style={"margin-bottom": "15px"}):
        with solara.Column():
            total = sum(archetype_dist.value.values())
            
            for archetype_name, archetype_info in ARCHETYPES.items():
                color = archetype_info['color']
                desc = archetype_info['description']
                current_val = archetype_dist.value[archetype_name]
                
                solara.Markdown(f"**{color} {archetype_name.replace('_', ' ').title()}**")
                solara.Markdown(f"*{desc}*")
                solara.SliderFloat(
                    label="",
                    value=current_val,
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    on_value=lambda v, name=archetype_name: archetype_dist.set({
                        **archetype_dist.value,
                        name: v
                    })
                )
                solara.Markdown(f"*{current_val:.0%} ({int(current_val * population_size.value)} agents)*")
            
            # Validation
            if abs(total - 1.0) < 0.01:
                solara.Success(f"✅ Total: {total:.0%}")
            else:
                solara.Error(f"⚠️ Total must equal 100% (currently {total:.0%})")


@solara.component
def SimulationControls():
    """Simulation control buttons"""
    with solara.Card("🎮 Simulation Controls", style={"margin-bottom": "15px"}):
        with solara.Column():
            with solara.Row():
                solara.Button(
                    "Create Model",
                    on_click=create_model,
                    color="primary",
                    outlined=True
                )
                
                if model_instance.value is not None:
                    solara.Button(
                        "▶ Run",
                        on_click=run_simulation,
                        color="success",
                        outlined=True
                    )
                    
                    solara.Button(
                        "↻ Reset",
                        on_click=reset_model,
                        color="error",
                        outlined=True
                    )
            
            # Max steps
            solara.Markdown("**Maximum Timesteps**")
            solara.SliderInt(
                label="",
                value=max_steps.value,
                min=50,
                max=500,
                step=50,
                on_value=max_steps.set
            )
            solara.Markdown(f"*Current: {max_steps.value} steps*")
            
            # Random seed
            solara.Markdown("**Random Seed (blank for random)**")
            solara.InputInt(
                label="",
                value=random_seed.value,
                on_value=random_seed.set
            )
            
            # Current status
            if model_instance.value is not None:
                solara.Info(f"📍 Current Step: {current_step.value} / {max_steps.value}")


@solara.component
def AdvancedSettings():
    """Advanced parameter settings"""
    with solara.Card("⚙️ Advanced Settings", style={"margin-bottom": "15px"}):
        with solara.Column():
            solara.Markdown("**Base Transition Rates**")
            
            solara.Markdown("Adoption Rate (σ₀)")
            solara.SliderFloat(
                label="",
                value=sigma_base.value,
                min=0.01,
                max=0.50,
                step=0.01,
                on_value=sigma_base.set
            )
            solara.Markdown(f"*{sigma_base.value:.2f} - Base E→I probability*")
            
            solara.Markdown("Correction Rate (γ₀)")
            solara.SliderFloat(
                label="",
                value=gamma_base.value,
                min=0.01,
                max=0.20,
                step=0.01,
                on_value=gamma_base.set
            )
            solara.Markdown(f"*{gamma_base.value:.2f} - Base I→R probability*")
            
            solara.Markdown("Relapse Rate (ω₀)")
            solara.SliderFloat(
                label="",
                value=omega_base.value,
                min=0.001,
                max=0.10,
                step=0.001,
                on_value=omega_base.set
            )
            solara.Markdown(f"*{omega_base.value:.3f} - Base R→S probability*")


# ============================================================================
# VISUALIZATION COMPONENTS
# ============================================================================

@solara.component
def R0Display():
    """Display R₀ calculation"""
    model = model_instance.value
    R0, components = model.calculate_R0()
    
    with solara.Card("📈 Theoretical Prediction (R₀)", style={"margin-bottom": "15px"}):
        if R0 > 1:
            indicator = "⚠️"
            message = "Epidemic will spread"
            color = "#ff9800"
        else:
            indicator = "✅"
            message = "Epidemic will die out"
            color = "#4caf50"
        
        solara.Markdown(f"""
### {indicator} Basic Reproduction Number: R₀ = {R0:.2f}
**Prediction:** {message}

**Components:**
- Mean exposure susceptibility (α): {components['mean_alpha']:.3f}
- Mean adoption rate (σ): {components['mean_sigma']:.3f}
- Mean network degree (k): {components['mean_degree']:.1f}
- Mean infectious period (1/γ): {components['infectious_period']:.1f} steps
        """)


@solara.component
def TrajectoryPlot():
    """Plot state trajectories over time"""
    model = model_instance.value
    df = model.datacollector.get_model_vars_dataframe()
    
    with solara.Card("📊 State Trajectories Over Time", style={"margin-bottom": "15px"}):
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(df.index, df['Susceptible'], 'g-', label='Susceptible (S)', linewidth=2.5, alpha=0.8)
        ax.plot(df.index, df['Exposed'], 'y-', label='Exposed (E)', linewidth=2.5, alpha=0.8)
        ax.plot(df.index, df['Infected'], 'r-', label='Infected (I)', linewidth=2.5, alpha=0.8)
        ax.plot(df.index, df['Recovered'], 'b-', label='Recovered (R)', linewidth=2.5, alpha=0.8)
        
        ax.set_xlabel('Timesteps', fontsize=13, fontweight='bold')
        ax.set_ylabel('Number of Agents', fontsize=13, fontweight='bold')
        ax.set_title('SEIRS State Dynamics', fontsize=15, fontweight='bold', pad=15)
        ax.legend(loc='best', fontsize=11, framealpha=0.9)
        ax.grid(True, alpha=0.25, linestyle='--')
        ax.set_xlim(0, max(df.index))
        ax.set_ylim(0, model.population * 1.05)
        
        plt.tight_layout()
        solara.FigureMatplotlib(fig)
        plt.close(fig)


@solara.component
def MetricsSummary():
    """Display peak metrics and archetype infection rates"""
    model = model_instance.value
    metrics = model.get_peak_metrics()
    rates = model.get_archetype_infection_rates()
    
    with solara.Card("📋 Metrics Summary", style={"margin-bottom": "15px"}):
        solara.Markdown(f"""
### Peak Prevalence Metrics

- **Maximum Infected:** {metrics['max_infected']} agents ({metrics['max_infected_pct']:.1%})
- **Time to Peak:** {metrics['time_to_peak']} timesteps
- **Final Attack Rate:** {metrics['attack_rate']:.1%} (proportion ever infected)

### Archetype-Specific Infection Rates
        """)
        
        for archetype_name, data in rates.items():
            color = ARCHETYPES[archetype_name]['color']
            pct = data['percentage']
            
            # Create simple progress bar using markdown
            filled = int(pct * 20)
            bar = '█' * filled + '░' * (20 - filled)
            
            solara.Markdown(f"""
**{color} {archetype_name.replace('_', ' ').title()}:** {data['infected']}/{data['total']} ({pct:.1%})  
`{bar}`
            """)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_model():
    """Create a new model instance"""
    # Validate archetype distribution
    total = sum(archetype_dist.value.values())
    if abs(total - 1.0) > 0.01:
        solara.Error(f"Archetype distribution must sum to 100% (currently {total:.0%})")
        return
    
    try:
        model = DisinformationModel(
            narrative_params=narrative_params.value,
            archetype_dist=archetype_dist.value,
            population=population_size.value,
            m_edges=m_edges.value,
            seeding_strategy=seeding_strategy.value,
            sigma_base=sigma_base.value,
            gamma_base=gamma_base.value,
            omega_base=omega_base.value,
            seed=random_seed.value if random_seed.value else None
        )
        
        model_instance.set(model)
        current_step.set(0)
        solara.Success(f"✅ Model created with {model.population} agents, R₀ = {model.calculate_R0()[0]:.2f}")
        
    except Exception as e:
        solara.Error(f"Error creating model: {str(e)}")


def run_simulation():
    """Run the simulation"""
    if model_instance.value is None:
        solara.Error("Please create a model first!")
        return
    
    try:
        model = model_instance.value
        model.run(max_steps=max_steps.value)
        
        current_step.set(model.current_step)
        model_instance.set(model)  # Force update
        
        metrics = model.get_peak_metrics()
        solara.Success(f"✅ Simulation complete! Peak: {metrics['max_infected']} infected at step {metrics['time_to_peak']}")
        
    except Exception as e:
        solara.Error(f"Error running simulation: {str(e)}")


def reset_model():
    """Reset the model"""
    model_instance.set(None)
    current_step.set(0)
    solara.Info("Model reset. Create a new model to continue.")


# Toggle advanced settings
@solara.component
def AdvancedToggle():
    """Toggle button for advanced settings"""
    if show_advanced.value:
        solara.Button(
            "▼ Hide Advanced Settings",
            on_click=lambda: show_advanced.set(False),
            text=True
        )
    else:
        solara.Button(
            "▶ Show Advanced Settings",
            on_click=lambda: show_advanced.set(True),
            text=True
        )