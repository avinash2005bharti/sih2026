from agents.base_agent import BaseAgent

class ReportingAgent(BaseAgent):
    def __init__(self):
        super().__init__("ReportingAgent")

reporting_agent = ReportingAgent()
