"""
Simple test to verify the model runs correctly.
"""

import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "layer2_sim"))

from layer2_sim.model import DisinformationModel  # model/model.py
from layer2_sim.model import ARCHETYPES      # model/archetypes.py

# Test parameters
narrative_params = {
    'baseline_transmission': 0.45,
    'emotional_intensity': 0.70,
    'identity_weight': 0.75,
    'initial_seeding': 0.06
}

archetype_dist = {name: ARCHETYPES[name]['distribution'] for name in ARCHETYPES.keys()}

print("Creating model...")
model = DisinformationModel(
    narrative_params=narrative_params,
    archetype_dist=archetype_dist,
    population=100,  # Small for quick test
    m_edges=3,
    seed=42
)

print(f"Model created with {model.population} agents")
print(f"Initial infected: {model._count_state(model, 'I')}")

# Calculate R0
R0, components = model.calculate_R0()
print(f"\nR₀ = {R0:.2f}")
print(f"  Mean α: {components['mean_alpha']:.3f}")
print(f"  Mean σ: {components['mean_sigma']:.3f}")
print(f"  Mean degree: {components['mean_degree']:.1f}")
print(f"  Infectious period: {components['infectious_period']:.1f} steps")

# Run simulation
print("\nRunning simulation for 50 steps...")
model.run(max_steps=50)

# Get metrics
metrics = model.get_peak_metrics()
print(f"\nPeak Metrics:")
print(f"  Max infected: {metrics['max_infected']} ({metrics['max_infected_pct']:.1%})")
print(f"  Time to peak: {metrics['time_to_peak']} steps")
print(f"  Attack rate: {metrics['attack_rate']:.1%}")

# Archetype infection rates
print(f"\nArchetype Infection Rates:")
rates = model.get_archetype_infection_rates()
for archetype, data in rates.items():
    print(f"  {archetype}: {data['infected']}/{data['total']} ({data['percentage']:.1%})")

print("\n✅ Test completed successfully!")