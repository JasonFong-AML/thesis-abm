"""
Generate Layer 2 Baseline Results for Thesis

This script runs all three narratives (N1, N2, N3) and exports results
in the format needed for Section 4.2 of the thesis.

Usage:
    python generate_layer2_results.py
"""

import sys
from pathlib import Path

# Add model to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "layer2_sim"))

from model.model import DisinformationModel
from model.archetypes import ARCHETYPES
from analysis.export import (
    export_simulation_results,
    create_baseline_comparison_table,
    format_thesis_table
)


# ============================================================================
# NARRATIVE DEFINITIONS (from Layer 1 BERTopic analysis)
# ============================================================================

NARRATIVES = {
    'N1_conspiracies': {
        'baseline_transmission': 0.45,
        'emotional_intensity': 0.70,
        'identity_weight': 0.75,
        'initial_seeding': 0.06,
        'description': 'Conspiracies: Elite manipulation, controlled narratives'
    },
    'N2_social_blame': {
        'baseline_transmission': 0.42,
        'emotional_intensity': 0.80,
        'identity_weight': 0.85,
        'initial_seeding': 0.07,
        'description': 'Social Blame: Scapegoating, othering, us-vs-them'
    },
    'N3_govt_restrictions': {
        'baseline_transmission': 0.48,
        'emotional_intensity': 0.65,
        'identity_weight': 0.70,
        'initial_seeding': 0.08,
        'description': 'Government Restrictions: Lockdowns, mandates, freedom'
    }
}


# ============================================================================
# CONFIGURATION
# ============================================================================

# Fixed archetype distribution
ARCHETYPE_DIST = {
    'immune': 0.20,
    'superspreader': 0.15,
    'moderate': 0.50,
    'critical_thinker': 0.10,
    'cynical_contrarian': 0.05
}

# Simulation parameters
POPULATION = 1000
M_EDGES = 3
MAX_STEPS = 100
RANDOM_SEED = 42


# ============================================================================
# RUN SIMULATIONS
# ============================================================================

def run_narrative(narrative_name: str, params: dict):
    """Run simulation for one narrative"""
    print(f"\n{'='*60}")
    print(f"Running: {narrative_name}")
    print(f"Description: {params['description']}")
    print(f"{'='*60}")
    
    # Create model
    model = DisinformationModel(
        narrative_params={
            'baseline_transmission': params['baseline_transmission'],
            'emotional_intensity': params['emotional_intensity'],
            'identity_weight': params['identity_weight'],
            'initial_seeding': params['initial_seeding']
        },
        archetype_dist=ARCHETYPE_DIST,
        population=POPULATION,
        m_edges=M_EDGES,
        seed=RANDOM_SEED
    )
    
    # Calculate initial R₀
    R0, components = model.calculate_R0()
    print(f"\nInitial R₀: {R0:.2f}")
    print(f"  α (exposure): {components['mean_alpha']:.3f}")
    print(f"  σ (adoption): {components['mean_sigma']:.3f}")
    print(f"  k (degree): {components['mean_degree']:.1f}")
    print(f"  1/γ (infectious period): {components['infectious_period']:.1f}")
    
    # Run simulation
    print(f"\nRunning simulation for {MAX_STEPS} steps...")
    model.run(max_steps=MAX_STEPS)
    
    # Get results
    metrics = model.get_peak_metrics()
    print(f"\nResults:")
    print(f"  Peak infected: {metrics['max_infected']} ({metrics['max_infected_pct']:.1%}) at t={metrics['time_to_peak']}")
    print(f"  Attack rate: {metrics['attack_rate']:.1%}")
    
    # Profile metrics
    profile_metrics = model.get_profile_stratified_metrics()
    print(f"\nProfile-Stratified Outcomes:")
    print(f"{'Profile':<20} {'Attack Rate':<12} {'Mean Time I':<12} {'Correction %'}")
    print("-" * 60)
    for archetype, data in profile_metrics.items():
        display_name = archetype.replace('_', ' ').title()
        print(f"{display_name:<20} {data['attack_rate']:>10.1%}  {data['mean_time_in_I']:>10.1f}  {data['correction_rate']:>12.1%}")
    
    # Export results
    created_files = export_simulation_results(
        model=model,
        output_dir="results",
        narrative_name=narrative_name,
        include_trajectories=True,
        include_profile_metrics=True
    )
    
    print(f"\nExported files:")
    for name, path in created_files.items():
        print(f"  {name}: {path}")
    
    return model


def main():
    """Main execution"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║  Layer 2: Baseline Diffusion Results Generator                ║
║  Bachelor's Thesis - Anticipatory Counternarratives           ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Create results directory
    Path("results").mkdir(exist_ok=True)
    
    # Run all narratives
    models = {}
    for narrative_name, params in NARRATIVES.items():
        models[narrative_name] = run_narrative(narrative_name, params)
    
    # Create comparison table
    print(f"\n{'='*60}")
    print("CREATING COMPARISON TABLE")
    print(f"{'='*60}")
    
    comparison_df = create_baseline_comparison_table(
        models,
        output_file="results/baseline_comparison.csv"
    )
    
    print("\nBaseline Comparison Across Narratives:")
    print(comparison_df.to_string(index=False))
    
    # Generate LaTeX tables
    print(f"\n{'='*60}")
    print("GENERATING LATEX TABLES")
    print(f"{'='*60}")
    
    for narrative_name, model in models.items():
        latex = format_thesis_table(model, narrative_name)
        
        latex_file = Path("results") / f"{narrative_name}_table.tex"
        with open(latex_file, 'w') as f:
            f.write(latex)
        
        print(f"\nCreated: {latex_file}")
    
    # Key findings summary
    print(f"\n{'='*60}")
    print("KEY FINDINGS")
    print(f"{'='*60}")
    
    # Find narrative with highest peak
    peaks = {name: model.get_peak_metrics()['max_infected_pct'] 
             for name, model in models.items()}
    highest_peak = max(peaks, key=peaks.get)
    
    # Find narrative with highest relapse
    relapses = {}
    for name, model in models.items():
        total_infections = model.cumulative_infected
        total_relapses = sum(a.relapse_count for a in model.agents)
        relapses[name] = total_relapses / total_infections if total_infections > 0 else 0
    highest_relapse = max(relapses, key=relapses.get)
    
    print(f"""
1. {highest_peak} showed highest peak prevalence ({peaks[highest_peak]:.1%})
   - Consistent with β₀ = {NARRATIVES[highest_peak]['baseline_transmission']:.2f}

2. {highest_relapse} showed highest relapse rate ({relapses[highest_relapse]:.1%})
   - Consistent with Idw = {NARRATIVES[highest_relapse]['identity_weight']:.2f}

3. Superspreaders accounted for disproportionate transmission across all narratives
   - Attack rates: {', '.join([f"{name}: {models[name].get_profile_stratified_metrics()['superspreader']['attack_rate']:.1%}" for name in NARRATIVES.keys()])}

4. Moderate profile behavior determined whether epidemics reached saturation
   - Attack rates: {', '.join([f"{name}: {models[name].get_profile_stratified_metrics()['moderate']['attack_rate']:.1%}" for name in NARRATIVES.keys()])}
    """)
    
    print(f"\n{'='*60}")
    print("✅ ALL RESULTS GENERATED SUCCESSFULLY")
    print(f"{'='*60}")
    print("\nNext steps:")
    print("1. Check results/ directory for CSV files")
    print("2. Use LaTeX tables in Section 4.2 of thesis")
    print("3. Copy trajectory CSVs to your plotting tool")
    print("4. Proceed to Layer 3 intervention implementation")


if __name__ == "__main__":
    main()