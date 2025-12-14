"""
Narrative parameter configuration for disinformation spread simulation.

Based on literature:
- Vosoughi et al. (2018): Baseline transmission
- Solovev & Pröllochs (2022): Emotional intensity
- Nyhan & Reifler (2010): Identity weight effects
"""

from dataclasses import dataclass


@dataclass
class Narrative:
    """
    Represents a disinformation narrative with four key characteristics.
    
    Attributes:
        baseline_transmission (float): Base contagion rate β₀ ∈ [0,1]
        emotional_intensity (float): Emotional amplification Emo ∈ [0,1]
        identity_weight (float): Identity-relevance Idw ∈ [0,1]
        initial_seeding (float): Initial infection proportion p₀ ∈ [0,1]
    """
    baseline_transmission: float  # β₀
    emotional_intensity: float    # Emo
    identity_weight: float        # Idw
    initial_seeding: float        # p₀
    
    def __post_init__(self):
        """Validate narrative parameters are in valid range."""
        for field_name in ['baseline_transmission', 'emotional_intensity', 
                          'identity_weight', 'initial_seeding']:
            value = getattr(self, field_name)
            if not 0 <= value <= 1:
                raise ValueError(f"{field_name} must be in [0, 1], got {value}")
    
    @property
    def effective_transmission(self) -> float:
        """
        Calculate effective transmission rate with emotional amplification.
        
        Returns:
            β_effective = β₀ × (1 + Emo)
        """
        return self.baseline_transmission * (1 + self.emotional_intensity)