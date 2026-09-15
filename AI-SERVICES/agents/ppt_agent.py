from agents.base_agent import BaseAgent
from core.logging import logger

class PPTAgent(BaseAgent):
    """Specialist agent for PowerPoint presentation generation."""

    def __init__(self):
        super().__init__("PPTAgent")

ppt_agent = PPTAgent()
