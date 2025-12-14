"""
Archetype definitions for agent psychographic profiles.

Based on:
- Petty & Cacioppo (1986): Need for Cognition
- Nyhan & Reifler (2010): Institutional Trust
- Tversky & Kahneman (1974): Confirmation Bias
- Tajfel & Turner (1979): Identity Alignment
"""

# Five fixed psychographic archetypes representing realistic population segments
ARCHETYPES = {
    'immune': {
        'nfc': 0.85,
        'trust': 0.80,
        'cb': 0.20,
        'ia': 0.30,
        'distribution': 0.20,
        'description': 'High analytical, high trust, low bias',
        'color': '⚪',
        'hex_color': '#FFFFFF'
    },
    'superspreader': {
        'nfc': 0.15,
        'trust': 0.20,
        'cb': 0.85,
        'ia': 0.90,
        'distribution': 0.15,
        'description': 'Low analytical, low trust, high bias',
        'color': '🔴',
        'hex_color': '#FF4444'
    },
    'moderate': {
        'nfc': 0.50,
        'trust': 0.50,
        'cb': 0.50,
        'ia': 0.50,
        'distribution': 0.50,
        'description': 'Balanced; "moveable middle"',
        'color': '🟡',
        'hex_color': '#FFDD44'
    },
    'critical_thinker': {
        'nfc': 0.90,
        'trust': 0.50,
        'cb': 0.25,
        'ia': 0.35,
        'distribution': 0.10,
        'description': 'Very high analytical, neutral trust',
        'color': '🔵',
        'hex_color': '#4444FF'
    },
    'cynical_contrarian': {
        'nfc': 0.60,
        'trust': 0.15,
        'cb': 0.70,
        'ia': 0.75,
        'distribution': 0.05,
        'description': 'Moderate analytical, very low trust',
        'color': '🟣',
        'hex_color': '#AA44FF'
    }
}


def validate_archetype_distribution(distribution: dict) -> bool:
    """
    Validate that archetype distribution sums to 1.0 (100%).
    
    Args:
        distribution: Dict mapping archetype names to proportions
        
    Returns:
        True if valid, False otherwise
    """
    total = sum(distribution.values())
    return abs(total - 1.0) < 0.001  # Allow small floating point error


def get_archetype_counts(population: int, distribution: dict) -> dict:
    """
    Calculate number of agents for each archetype.
    
    Args:
        population: Total population size
        distribution: Dict mapping archetype names to proportions
        
    Returns:
        Dict mapping archetype names to agent counts
    """
    counts = {
        archetype: int(population * proportion)
        for archetype, proportion in distribution.items()
    }
    
    # Handle rounding - add remaining to 'moderate' (largest group)
    total = sum(counts.values())
    if total < population:
        counts['moderate'] += (population - total)
    elif total > population:
        counts['moderate'] -= (total - population)
    
    return counts


# State color mappings for visualization
STATE_COLORS = {
    'S': '#00FF00',  # Green - Susceptible
    'E': '#FFFF00',  # Yellow - Exposed
    'I': '#FF0000',  # Red - Infected
    'R': '#0000FF',  # Blue - Recovered
}

STATE_LABELS = {
    'S': 'Susceptible',
    'E': 'Exposed',
    'I': 'Infected',
    'R': 'Recovered',
}