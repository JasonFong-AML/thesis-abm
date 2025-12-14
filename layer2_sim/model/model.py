"""
Main model for SEIRS disinformation spread simulation.

Implements:
- Scale-free network generation (Barabási-Albert)
- Agent initialization with archetype distribution
- Initial seeding strategies
- Data collection for metrics
- R₀ calculation
"""

import mesa
from mesa import Model, DataCollector
import networkx as nx
import numpy as np
from typing import Optional

from .agent import DisinformationAgent
from .narrative import Narrative
from .archetypes import ARCHETYPES, get_archetype_counts, validate_archetype_distribution


class DisinformationModel(Model):
    """
    SEIRS model for disinformation spread on scale-free networks.
    
    Attributes:
        narrative: Narrative parameters (β₀, Emo, Idw, p₀)
        population: Number of agents
        G: NetworkX scale-free graph
        datacollector: Mesa DataCollector for metrics
        cumulative_infected: Total ever infected (for attack rate)
    """
    
    def __init__(
        self,
        narrative_params: dict,
        archetype_dist: dict,
        population: int = 1000,
        m_edges: int = 3,
        seeding_strategy: str = 'random',
        sigma_base: float = 0.30,
        gamma_base: float = 0.05,
        omega_base: float = 0.02,
        seed: Optional[int] = None
    ):
        """
        Initialize the disinformation spread model.
        
        Args:
            narrative_params: Dict with keys (baseline_transmission, emotional_intensity, 
                            identity_weight, initial_seeding)
            archetype_dist: Dict mapping archetype names to proportions (must sum to 1.0)
            population: Total number of agents
            m_edges: Edges per node in scale-free network
            seeding_strategy: 'random', 'hub_targeted', or 'archetype_proportional'
            sigma_base: Base adoption rate (E→I)
            gamma_base: Base correction rate (I→R)
            omega_base: Base relapse rate (R→S)
            seed: Random seed for reproducibility
        """
        super().__init__(seed=seed)
        
        # Validate archetype distribution
        if not validate_archetype_distribution(archetype_dist):
            raise ValueError("Archetype distribution must sum to 1.0")
        
        # Model parameters
        self.narrative = Narrative(**narrative_params)
        self.population = population
        self.m_edges = m_edges
        self.seeding_strategy = seeding_strategy
        
        # Base transition rates
        self.sigma_base = sigma_base
        self.gamma_base = gamma_base
        self.omega_base = omega_base
        
        # Metrics tracking
        self.cumulative_infected = 0
        self.current_step = 0
        
        # Create network
        self.G = self._create_network()
        
        # Create agents (Mesa 3.x manages agents internally)
        self._create_agents(archetype_dist)
        
        # Initial seeding
        self._seed_initial_infections()
        
        # Data collection
        self.datacollector = self._setup_datacollector()
        self.datacollector.collect(self)
    
    # ============================================================================
    # INITIALIZATION METHODS
    # ============================================================================
    
    def _create_network(self) -> nx.Graph:
        """
        Create scale-free network using Barabási-Albert model.
        
        Returns:
            NetworkX graph
        """
        return nx.barabasi_albert_graph(n=self.population, m=self.m_edges, seed=self._seed)
    
    def _create_agents(self, archetype_dist: dict):
        """
        Create agents based on archetype distribution.
        
        Args:
            archetype_dist: Dict mapping archetype names to proportions
        """
        # Calculate counts for each archetype
        archetype_counts = get_archetype_counts(self.population, archetype_dist)
        
        agent_id = 0
        for archetype_name, count in archetype_counts.items():
            archetype_params = ARCHETYPES[archetype_name]
            
            for _ in range(count):
                agent = DisinformationAgent(
                    model=self,
                    unique_id=agent_id,
                    archetype=archetype_name,
                    need_for_cognition=archetype_params['nfc'],
                    institutional_trust=archetype_params['trust'],
                    confirmation_bias=archetype_params['cb'],
                    identity_alignment=archetype_params['ia']
                )
                # Mesa 3.x auto-registers agents
                agent_id += 1
    
    def _seed_initial_infections(self):
        """
        Seed initial infections based on seeding strategy.
        """
        n_seed = int(self.population * self.narrative.initial_seeding)
        
        if n_seed == 0:
            n_seed = 1  # Ensure at least one seed
        
        agent_list = list(self.agents)
        
        if self.seeding_strategy == 'random':
            seed_agents = self.random.sample(agent_list, n_seed)
        
        elif self.seeding_strategy == 'hub_targeted':
            # Seed high-degree nodes
            degrees = dict(self.G.degree())
            sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
            seed_ids = [node_id for node_id, _ in sorted_nodes[:n_seed]]
            seed_agents = [a for a in agent_list if a.unique_id in seed_ids]
        
        elif self.seeding_strategy == 'archetype_proportional':
            # Seed according to archetype distribution
            seed_agents = []
            for archetype_name, proportion in ARCHETYPES.items():
                archetype_agents = [a for a in agent_list if a.archetype == archetype_name]
                n_archetype_seed = int(n_seed * ARCHETYPES[archetype_name]['distribution'])
                if n_archetype_seed > 0 and archetype_agents:
                    seeds = self.random.sample(archetype_agents, min(n_archetype_seed, len(archetype_agents)))
                    seed_agents.extend(seeds)
        
        else:
            raise ValueError(f"Unknown seeding strategy: {self.seeding_strategy}")
        
        # Set initial infections
        for agent in seed_agents:
            agent.state = 'I'
            self.cumulative_infected += 1
    
    def _setup_datacollector(self) -> DataCollector:
        """
        Setup data collector for tracking metrics.
        
        Returns:
            Configured DataCollector
        """
        return DataCollector(
            model_reporters={
                # State counts
                "Susceptible": lambda m: self._count_state(m, 'S'),
                "Exposed": lambda m: self._count_state(m, 'E'),
                "Infected": lambda m: self._count_state(m, 'I'),
                "Recovered": lambda m: self._count_state(m, 'R'),
                "Cumulative_Infected": lambda m: m.cumulative_infected,
                
                # Archetype-specific infected counts
                "Infected_Immune": lambda m: self._count_infected_archetype(m, 'immune'),
                "Infected_Superspreader": lambda m: self._count_infected_archetype(m, 'superspreader'),
                "Infected_Moderate": lambda m: self._count_infected_archetype(m, 'moderate'),
                "Infected_Critical": lambda m: self._count_infected_archetype(m, 'critical_thinker'),
                "Infected_Cynical": lambda m: self._count_infected_archetype(m, 'cynical_contrarian'),
            }
        )
    
    # ============================================================================
    # SIMULATION METHODS
    # ============================================================================
    
    def step(self):
        """
        Run one timestep of the simulation with simultaneous activation.
        All agents calculate next state, then all advance simultaneously.
        """
        # Step 1: All agents calculate their next state
        for agent in self.agents:
            agent.step()
        
        # Step 2: All agents advance to next state simultaneously
        for agent in self.agents:
            agent.advance()
        
        # Collect data
        self.datacollector.collect(self)
        self.current_step += 1
    
    def run(self, max_steps: int = 100):
        """
        Run simulation for specified number of steps.
        
        Args:
            max_steps: Maximum timesteps to simulate
        """
        for _ in range(max_steps):
            self.step()
            
            # Early stopping if epidemic ends
            if self._epidemic_ended():
                break
    
    def _epidemic_ended(self) -> bool:
        """
        Check if epidemic has ended (no more E or I agents).
        
        Returns:
            True if ended, False otherwise
        """
        return (self._count_state(self, 'E') == 0 and 
                self._count_state(self, 'I') == 0)
    
    # ============================================================================
    # METRICS & ANALYSIS
    # ============================================================================
    
    def calculate_R0(self) -> tuple[float, dict]:
        """
        Calculate basic reproduction number.
        
        R₀ = <α> × <σ> × <k> × (1/<γ>)
        
        Returns:
            Tuple of (R0 value, components dict)
        """
        alphas = []
        sigmas = []
        gammas = []
        
        for agent in self.agents:
            alphas.append(agent._calculate_alpha(self.narrative))
            sigmas.append(agent._calculate_sigma(self.narrative))
            gammas.append(agent._calculate_gamma(self.narrative))
        
        mean_alpha = np.mean(alphas)
        mean_sigma = np.mean(sigmas)
        mean_gamma = np.mean(gammas)
        mean_degree = np.mean([self.G.degree(n) for n in self.G.nodes()])
        
        infectious_period = 1 / mean_gamma if mean_gamma > 0 else np.inf
        
        R0 = mean_alpha * mean_sigma * mean_degree * infectious_period
        
        components = {
            'mean_alpha': mean_alpha,
            'mean_sigma': mean_sigma,
            'mean_gamma': mean_gamma,
            'mean_degree': mean_degree,
            'infectious_period': infectious_period
        }
        
        return R0, components
    
    def get_peak_metrics(self) -> dict:
        """
        Calculate peak prevalence metrics from collected data.
        
        Returns:
            Dict with max_infected, time_to_peak, attack_rate
        """
        df = self.datacollector.get_model_vars_dataframe()
        
        max_infected = df['Infected'].max()
        time_to_peak = df['Infected'].idxmax()
        attack_rate = df['Cumulative_Infected'].iloc[-1] / self.population
        
        return {
            'max_infected': int(max_infected),
            'max_infected_pct': max_infected / self.population,
            'time_to_peak': int(time_to_peak),
            'attack_rate': attack_rate
        }
    
    def get_archetype_infection_rates(self) -> dict:
        """
        Calculate final infection rates by archetype.
        
        Returns:
            Dict mapping archetype to (infected_count, total_count, percentage)
        """
        rates = {}
        
        for archetype_name in ARCHETYPES.keys():
            archetype_agents = [a for a in self.agents if a.archetype == archetype_name]
            total = len(archetype_agents)
            infected = len([a for a in archetype_agents if a.state == 'I'])
            
            rates[archetype_name] = {
                'infected': infected,
                'total': total,
                'percentage': infected / total if total > 0 else 0
            }
        
        return rates
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    @staticmethod
    def _count_state(model: 'DisinformationModel', state: str) -> int:
        """Count agents in specified state."""
        return sum(1 for a in model.agents if a.state == state)
    
    @staticmethod
    def _count_infected_archetype(model: 'DisinformationModel', archetype: str) -> int:
        """Count infected agents of specified archetype."""
        return sum(1 for a in model.agents 
                  if a.state == 'I' and a.archetype == archetype)