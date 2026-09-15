from agents.base_agent import BaseAgent

class SafetyAgent(BaseAgent):
    def __init__(self):
        super().__init__("SafetyAgent")

safety_agent = SafetyAgent()
