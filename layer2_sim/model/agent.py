"""
Agent implementation for SEIRS disinformation spread model.

Agents transition through states: S → E → I → R → S
Each transition is modulated by agent psychographic traits and narrative parameters.
"""

import mesa
import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import DisinformationModel
    from .narrative import Narrative


class DisinformationAgent(mesa.Agent):
    """
    Agent with psychographic traits that determine susceptibility to disinformation.
    
    Attributes:
        archetype (str): Profile type ('immune', 'superspreader', etc.)
        need_for_cognition (float): Analytical thinking depth [0,1]
        institutional_trust (float): Trust in authorities [0,1]
        confirmation_bias (float): Motivated reasoning [0,1]
        identity_alignment (float): Narrative-identity match [0,1]
        state (str): Current SEIRS state ('S', 'E', 'I', 'R')
    """
    
    def __init__(
        self,
        model: 'DisinformationModel',
        unique_id: int,
        archetype: str,
        need_for_cognition: float,
        institutional_trust: float,
        confirmation_bias: float,
        identity_alignment: float
    ):
        super().__init__(model)
        
        # Store unique_id (Mesa 3.x doesn't store it automatically)
        self.unique_id = unique_id
        
        # Archetype and traits
        self.archetype = archetype
        self.need_for_cognition = need_for_cognition
        self.institutional_trust = institutional_trust
        self.confirmation_bias = confirmation_bias
        self.identity_alignment = identity_alignment
        
        # State tracking
        self.state = 'S'  # Start susceptible (unless seeded)
        self.next_state = None  # For simultaneous activation
        
        # History tracking for metrics
        self.infection_count = 0  # Number of times entered I state
        self.recovery_count = 0   # Number of times I → R
        self.relapse_count = 0    # Number of times R → S
        self.time_in_I = 0        # Cumulative timesteps in I state
        self.current_I_duration = 0  # Current infection spell duration
        
    # ============================================================================
    # STATE TRANSITION LOGIC
    # ============================================================================
    
    def step(self):
        """
        Calculate next state based on current state.
        Called by SimultaneousActivation scheduler.
        """
        if self.state == 'S':
            self.next_state = self._check_exposure()
        elif self.state == 'E':
            self.next_state = self._check_adoption()
        elif self.state == 'I':
            self.next_state = self._check_correction()
        elif self.state == 'R':
            self.next_state = self._check_relapse()
    
    def advance(self):
        """
        Commit state transition and track history.
        Called by SimultaneousActivation after all agents have stepped.
        """
        if self.next_state:
            old_state = self.state
            self.state = self.next_state
            self.next_state = None
            
            # Track transitions for metrics
            if old_state != 'I' and self.state == 'I':
                # Entering I state
                self.model.cumulative_infected += 1
                self.infection_count += 1
                self.current_I_duration = 0
            
            if old_state == 'I' and self.state == 'R':
                # I → R: Successful correction
                self.recovery_count += 1
            
            if old_state == 'R' and self.state == 'S':
                # R → S: Relapse
                self.relapse_count += 1
            
            # Track time in I
            if self.state == 'I':
                self.time_in_I += 1
                self.current_I_duration += 1
    
    # ============================================================================
    # TRANSITION CHECKS
    # ============================================================================
    
    def _check_exposure(self) -> str:
        """
        S → E transition: Exposure through infected neighbors.
        
        Returns:
            'E' if exposed, 'S' if remains susceptible
        """
        infected_neighbors = self._get_infected_neighbors()
        
        if not infected_neighbors:
            return 'S'
        
        # Calculate exposure probability
        alpha = self._calculate_alpha(self.model.narrative)
        
        # Compound probability from multiple infected neighbors
        # P(exposed) = 1 - (1 - α)^k where k = number of infected neighbors
        k = len(infected_neighbors)
        p_exposure = 1 - (1 - alpha) ** k
        
        if self.random.random() < p_exposure:
            return 'E'
        
        return 'S'
    
    def _check_adoption(self) -> str:
        """
        E → I transition: Adoption through cognitive processing.
        
        Returns:
            'I' if adopted, 'E' if remains exposed
        """
        sigma = self._calculate_sigma(self.model.narrative)
        
        if self.random.random() < sigma:
            return 'I'
        
        return 'E'
    
    def _check_correction(self) -> str:
        """
        I → R transition: Correction through fact-checking or analytical reconsideration.
        
        Returns:
            'R' if corrected, 'I' if remains infected
        """
        gamma = self._calculate_gamma(self.model.narrative)
        
        if self.random.random() < gamma:
            return 'R'
        
        return 'I'
    
    def _check_relapse(self) -> str:
        """
        R → S transition: Relapse due to waning immunity.
        
        Returns:
            'S' if relapsed, 'R' if remains recovered
        """
        omega = self._calculate_omega(self.model.narrative)
        
        if self.random.random() < omega:
            return 'S'
        
        return 'R'
    
    # ============================================================================
    # TRANSITION PROBABILITY CALCULATIONS
    # ============================================================================
    
    def _calculate_alpha(self, narrative: 'Narrative') -> float:
        """
        Calculate exposure susceptibility (S → E rate).
        
        α = β₀ × (1 + Emo) × susceptibility_multiplier
        
        Agent trait effects:
        - High NFC → reduces exposure (critical filtering)
        - High CB → increases exposure (motivated seeking)
        - High IA → increases exposure (identity-motivated)
        
        Args:
            narrative: Narrative parameters
            
        Returns:
            Probability of exposure per infected neighbor
        """
        # Base transmission with emotional amplification
        base = narrative.effective_transmission
        
        # Agent-specific susceptibility multiplier
        effect = (
            -0.6 * (self.need_for_cognition - 0.5) +      # High NFC filters
            0.0 * (self.institutional_trust - 0.5) +      # Trust neutral for exposure
            +0.4 * (self.confirmation_bias - 0.5) +       # High CB seeks congruent content
            +0.3 * (self.identity_alignment - 0.5) * narrative.identity_weight  # Identity-motivated
        )
        
        susceptibility = np.clip(1.0 + effect, 0.1, 2.0)
        
        alpha = base * susceptibility
        return np.clip(alpha, 0.0, 1.0)
    
    def _calculate_sigma(self, narrative: 'Narrative') -> float:
        """
        Calculate adoption rate (E → I).
        
        σ = σ₀ × adoption_multiplier
        
        Agent trait effects:
        - High NFC → reduces adoption (scrutiny)
        - High Trust → reduces adoption (trusts debunking)
        - High CB → increases adoption (reduced scrutiny)
        - High IA × Idw → amplifies adoption (identity-protective)
        
        Args:
            narrative: Narrative parameters
            
        Returns:
            Probability of adoption per timestep
        """
        base_adoption = self.model.sigma_base
        
        # Agent-specific adoption multiplier
        effect = (
            -0.7 * (self.need_for_cognition - 0.5) +      # High NFC scrutinizes
            -0.5 * (self.institutional_trust - 0.5) +     # High trust resists
            +0.6 * (self.confirmation_bias - 0.5) +       # High CB reduces scrutiny
            +1.0 * (self.identity_alignment - 0.5) * narrative.identity_weight  # Identity amplification
        )
        
        multiplier = np.clip(1.0 + effect, 0.1, 3.0)
        
        sigma = base_adoption * multiplier
        return np.clip(sigma, 0.0, 1.0)
    
    def _calculate_gamma(self, narrative: 'Narrative') -> float:
        """
        Calculate correction rate (I → R).
        
        γ = γ₀ × (1 + boosts) / (1 + penalties)
        
        Agent trait effects:
        - High NFC → increases correction (self-correction)
        - High Trust → increases correction (accepts authorities)
        - High CB → reduces correction (resists disconfirmation)
        - High IA × Idw → reduces correction (identity protection)
        
        Args:
            narrative: Narrative parameters
            
        Returns:
            Probability of correction per timestep
        """
        base_correction = self.model.gamma_base
        
        # Boosting factors
        nfc_boost = self.need_for_cognition * 0.8
        trust_boost = self.institutional_trust * 0.6
        
        # Penalty factors
        cb_penalty = self.confirmation_bias * 0.5
        ia_penalty = self.identity_alignment * narrative.identity_weight * 0.8
        
        multiplier = (1 + nfc_boost + trust_boost) / (1 + cb_penalty + ia_penalty)
        
        gamma = base_correction * multiplier
        return np.clip(gamma, 0.0, 1.0)
    
    def _calculate_omega(self, narrative: 'Narrative') -> float:
        """
        Calculate relapse rate (R → S).
        
        ω = ω₀ × (1 + amplifications) / (1 + protections)
        
        Agent trait effects:
        - Low Trust → increases relapse (corrections fade)
        - High IA × Idw → increases relapse (identity-driven)
        - High NFC → reduces relapse (sustained revision)
        
        Args:
            narrative: Narrative parameters
            
        Returns:
            Probability of relapse per timestep
        """
        base_waning = self.model.omega_base
        
        # Amplification factors
        trust_penalty = (1 - self.institutional_trust) * 0.6
        ia_amplification = self.identity_alignment * narrative.identity_weight * 1.0
        
        # Reduction factors
        nfc_protection = self.need_for_cognition * 0.4
        
        multiplier = (1 + trust_penalty + ia_amplification) / (1 + nfc_protection)
        
        omega = base_waning * multiplier
        return np.clip(omega, 0.0, 0.2)  # Cap at 20% per timestep
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _get_infected_neighbors(self) -> list:
        """
        Get list of neighboring agents in 'I' state.
        
        Returns:
            List of neighbor agent IDs
        """
        # Create a dict for fast lookup
        agents_dict = {a.unique_id: a for a in self.model.agents}
        
        infected = []
        for neighbor_id in self.model.G.neighbors(self.unique_id):
            neighbor = agents_dict.get(neighbor_id)
            if neighbor and neighbor.state == 'I':
                infected.append(neighbor_id)
        return infected