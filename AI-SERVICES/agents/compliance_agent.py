from agents.base_agent import BaseAgent

class ComplianceAgent(BaseAgent):
    def __init__(self):
        super().__init__("ComplianceAgent")

compliance_agent = ComplianceAgent()
