"""
Analysis utilities for Layer 2 SEIRS model.
Includes data export and summary statistics.
"""

import pandas as pd
from pathlib import Path
from typing import Optional


def export_simulation_results(
    model,
    output_dir: str = "results",
    narrative_name: str = "N1_conspiracies",
    include_trajectories: bool = True,
    include_profile_metrics: bool = True
) -> dict:
    """
    Export simulation results to CSV files.
    
    Args:
        model: DisinformationModel instance (after running)
        output_dir: Directory to save results
        narrative_name: Name identifier for this narrative
        include_trajectories: Export S/E/I/R time series
        include_profile_metrics: Export profile-stratified metrics
    
    Returns:
        dict: Paths to created files
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    created_files = {}
    
    # 1. Overall metrics
    metrics = model.get_peak_metrics()
    R0, components = model.calculate_R0()
    
    overall_df = pd.DataFrame([{
        'narrative': narrative_name,
        'R0': R0,
        'mean_alpha': components['mean_alpha'],
        'mean_sigma': components['mean_sigma'],
        'mean_gamma': components['mean_gamma'],
        'mean_degree': components['mean_degree'],
        'infectious_period': components['infectious_period'],
        'peak_infected': metrics['max_infected'],
        'peak_infected_pct': metrics['max_infected_pct'],
        'time_to_peak': metrics['time_to_peak'],
        'attack_rate': metrics['attack_rate'],
        'population': model.population,
        'total_steps': model.current_step
    }])
    
    overall_file = output_path / f"{narrative_name}_overall_metrics.csv"
    overall_df.to_csv(overall_file, index=False)
    created_files['overall'] = str(overall_file)
    
    # 2. Profile-stratified metrics
    if include_profile_metrics:
        profile_data = model.get_profile_stratified_metrics()
        
        profile_rows = []
        for archetype, data in profile_data.items():
            profile_rows.append({
                'narrative': narrative_name,
                'profile': archetype,
                'total_agents': data['total_agents'],
                'ever_infected': data['ever_infected'],
                'attack_rate': data['attack_rate'],
                'mean_time_in_I': data['mean_time_in_I'],
                'total_infections': data['total_infections'],
                'total_recoveries': data['total_recoveries'],
                'correction_rate': data['correction_rate'],
                'mean_relapses': data['mean_relapses']
            })
        
        profile_df = pd.DataFrame(profile_rows)
        profile_file = output_path / f"{narrative_name}_profile_metrics.csv"
        profile_df.to_csv(profile_file, index=False)
        created_files['profiles'] = str(profile_file)
    
    # 3. State trajectories
    if include_trajectories:
        traj_df = model.datacollector.get_model_vars_dataframe()
        traj_df['narrative'] = narrative_name
        
        traj_file = output_path / f"{narrative_name}_trajectories.csv"
        traj_df.to_csv(traj_file)
        created_files['trajectories'] = str(traj_file)
    
    return created_files


def create_baseline_comparison_table(
    results: dict,
    output_file: str = "baseline_comparison.csv"
) -> pd.DataFrame:
    """
    Create comparison table across multiple narratives.
    
    Args:
        results: Dict mapping narrative names to model instances
                 e.g., {'N1': model1, 'N2': model2, 'N3': model3}
        output_file: Path to save CSV
    
    Returns:
        DataFrame with comparison metrics
    """
    rows = []
    
    for narrative_name, model in results.items():
        metrics = model.get_peak_metrics()
        R0, components = model.calculate_R0()
        
        # Calculate relapse rate
        total_infections = model.cumulative_infected
        total_relapses = sum(a.relapse_count for a in model.agents)
        relapse_rate = total_relapses / total_infections if total_infections > 0 else 0.0
        
        rows.append({
            'Narrative': narrative_name,
            'R₀': f"{R0:.2f}",
            'Peak I(t)': f"{metrics['max_infected_pct']:.1%}",
            'Time to Peak': metrics['time_to_peak'],
            'Attack Rate': f"{metrics['attack_rate']:.1%}",
            'Relapse Rate': f"{relapse_rate:.1%}"
        })
    
    df = pd.DataFrame(rows)
    
    if output_file:
        df.to_csv(output_file, index=False)
        print(f"Saved comparison table to {output_file}")
    
    return df


def format_thesis_table(
    model,
    narrative_name: str = "N1"
) -> str:
    """
    Generate LaTeX-formatted table for thesis.
    
    Args:
        model: DisinformationModel instance
        narrative_name: Narrative identifier
    
    Returns:
        str: LaTeX table code
    """
    profile_data = model.get_profile_stratified_metrics()
    
    latex = f"""
\\begin{{table}}[h]
\\centering
\\caption{{Profile-Stratified Outcomes for {narrative_name}}}
\\begin{{tabular}}{{llll}}
\\toprule
Profile & Attack Rate & Mean Time in I & Correction Rate \\\\
\\midrule
"""
    
    for archetype, data in profile_data.items():
        display_name = archetype.replace('_', ' ').title()
        latex += f"{display_name} & "
        latex += f"{data['attack_rate']:.1%} & "
        latex += f"{data['mean_time_in_I']:.1f} & "
        latex += f"{data['correction_rate']:.1%} \\\\\n"
    
    latex += """\\bottomrule
\\end{tabular}
\\end{table}
"""
    
    return latex


def run_multiple_seeds(
    narrative_params: dict,
    archetype_dist: dict,
    seeds: list,
    population: int = 1000,
    max_steps: int = 100,
    **kwargs
) -> pd.DataFrame:
    """
    Run simulation with multiple random seeds for statistical analysis.
    
    Args:
        narrative_params: Narrative configuration
        archetype_dist: Archetype distribution
        seeds: List of random seeds to use
        population: Population size
        max_steps: Maximum simulation steps
        **kwargs: Additional model parameters
    
    Returns:
        DataFrame with results from all runs
    """
    from model.model import DisinformationModel
    
    results = []
    
    for seed in seeds:
        model = DisinformationModel(
            narrative_params=narrative_params,
            archetype_dist=archetype_dist,
            population=population,
            seed=seed,
            **kwargs
        )
        
        model.run(max_steps=max_steps)
        
        metrics = model.get_peak_metrics()
        R0, _ = model.calculate_R0()
        
        results.append({
            'seed': seed,
            'R0': R0,
            'peak_infected': metrics['max_infected'],
            'peak_infected_pct': metrics['max_infected_pct'],
            'time_to_peak': metrics['time_to_peak'],
            'attack_rate': metrics['attack_rate']
        })
    
    df = pd.DataFrame(results)
    
    # Add summary statistics
    print("\n=== Summary Statistics (n={}) ===".format(len(seeds)))
    print(df.describe())
    
    return df