from agents.base_agent import BaseAgent

class DocumentAgent(BaseAgent):
    def __init__(self):
        super().__init__("DocumentAgent")

document_agent = DocumentAgent()
