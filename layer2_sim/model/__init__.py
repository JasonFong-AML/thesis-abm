"""
SEIRS Disinformation Spread Model - Layer 2 Implementation

Core components:
- DisinformationAgent: Agents with psychographic traits
- DisinformationModel: Network-based epidemic model
- Narrative: Disinformation narrative parameters
- ARCHETYPES: Five psychographic profiles
"""

from .agent import DisinformationAgent
from .model import DisinformationModel
from .narrative import Narrative
from .archetypes import ARCHETYPES, STATE_COLORS, STATE_LABELS

__all__ = [
    'DisinformationAgent',
    'DisinformationModel',
    'Narrative',
    'ARCHETYPES',
    'STATE_COLORS',
    'STATE_LABELS',
]