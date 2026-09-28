import sys
sys.path.insert(0, './AI-SERVICES')
from llm.model_router import model_router

test_cases = [
    "Explain what a P&ID is.",
    "Write Python code to calculate the average of a list.",
    "Create an Excel file from this dataset.",
    "Create a PDF inspection report from these findings.",
    "Extract all visible text from this image.",
    "Identify this industrial component.",
    "What was the pressure recorded in Unit 4 in the document?"
]

print("=== MODEL ROUTER ROUTING TEST ===")
for q in test_cases:
    res = model_router.rule_based_route(q)
    model = model_router.route(q)
    intent = res.get("intent") if res else "general"
    agent = res.get("agent") if res else "general"
    print(f"Query: {q}")
    print(f"  -> Intent: {intent} | Agent: {agent} | Model: {model.selected_model}")
