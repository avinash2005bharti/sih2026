from agents.base_agent import BaseAgent

class MaintenanceAgent(BaseAgent):
    def __init__(self):
        super().__init__("MaintenanceAgent")

maintenance_agent = MaintenanceAgent()
