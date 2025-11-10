# model.py — Mesa 3.3.1 + SolaraViz working model (final)

from mesa.agent import Agent
from mesa.model import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import random


# ---------------------------------------------------------------------
#  Simple scheduler (mesa.time removed in 3.3)
# ---------------------------------------------------------------------
class RandomActivation:
    """Activate all agents once per step in random order."""
    def __init__(self, model):
        self.model = model
        self.agents = []

    def add(self, agent):
        self.agents.append(agent)

    def step(self):
        random.shuffle(self.agents)
        for agent in self.agents:
            agent.step()


# ---------------------------------------------------------------------
#  Agent
# ---------------------------------------------------------------------
class MyAgent(Agent):
    """A minimal agent that tracks its own position."""
    def __init__(self, unique_id=None, model=None, **kwargs):
        # Mesa 3.3 base Agent has no __init__ args — skip super()
        self.unique_id = unique_id
        self.model = model
        self.pos = None  # ✅ required by MultiGrid.place_agent()

    def step(self):
        pass


# ---------------------------------------------------------------------
#  Model
# ---------------------------------------------------------------------
class MyModel(Model):
    """A simple grid-based model compatible with Mesa 3.3 + Solara."""
    def __init__(self, N=10, width=10, height=10):
        # ✅ explicit RNG and step counter
        self._rng = random.Random()
        self.steps = 0
        self.num_agents = N
        self.grid = MultiGrid(width, height, torus=True)
        self.schedule = RandomActivation(self)
        self.running = True

        # Create and place agents
        for i in range(self.num_agents):
            a = MyAgent(unique_id=i, model=self)
            self.schedule.add(a)
            x = self._rng.randrange(self.grid.width)
            y = self._rng.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))

        # Simple metric collection
        self.datacollector = DataCollector(
            model_reporters={"NumAgents": lambda m: len(m.schedule.agents)}
        )

    def step(self):
        """Advance the model by one tick."""
        self.datacollector.collect(self)
        self.schedule.step()
        self.steps += 1   # ✅ required by SolaraViz
