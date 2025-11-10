# server.py — Mesa 3.3 + Solara visualization entry point

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import solara
from mesa.visualization import solara_viz
from model import MyModel


# ---------------------------------------------------------------------
#  Agent portrayal for the grid view
# ---------------------------------------------------------------------
def agent_portrayal(agent):
    return {
        "Shape": "circle",
        "Color": "royalblue",
        "Filled": "true",
        "Layer": 0,
        "r": 0.8,
    }


# ---------------------------------------------------------------------
#  Create a model instance for visualization
# ---------------------------------------------------------------------
model = MyModel(N=10, width=10, height=10)


# ---------------------------------------------------------------------
#  Solara expects a top-level component called Page
# ---------------------------------------------------------------------
@solara.component
def Page():
    """Top-level Solara component rendered by `solara run server.py`."""
    return solara_viz.SolaraViz(
        model,
        name="MyModel ABM",
        description="A minimal agent-based model using Mesa 3.3 + Solara.",
        portrayal_method=agent_portrayal,
        space="grid",
    )
