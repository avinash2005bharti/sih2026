"""
Sync MongoDB agents collection with Document Section access and tools.
"""
import sys
import pymongo

DOC_DIRECTIVE = """
DOCUMENT SECTION & REPOSITORY ACCESS:
- You have complete access to the Document Section and all workspace documents, files, and repository data.
- You can list, inspect, read, search, and analyze any uploaded document using available tools:
  - list_documents: View all documents in the document section.
  - get_document: Retrieve document metadata and status.
  - get_document_content: Read the full text content of any document.
  - search_database_documents: Search documents in the database by query.
- Never claim that you cannot access, see, or track documents in the workspace or document section.
"""

DOCUMENT_TOOLS = [
    "list_documents",
    "get_document",
    "get_document_content",
    "search_database_documents",
    "create_document",
    "update_document"
]

def sync_agents():
    client = pymongo.MongoClient("mongodb://admin:admin@localhost:27017/?authSource=admin")
    db = client["sovereign_ai"]
    agents = list(db.agents.find({}))
    print(f"Found {len(agents)} agents in MongoDB 'agents' collection.")

    for a in agents:
        slug = a.get("slug") or a.get("name")
        curr_prompt = a.get("systemPrompt") or ""
        curr_caps = a.get("capabilities") or []
        curr_tools = a.get("tools") or []

        new_caps = list(dict.fromkeys(curr_caps + ["document_access", "document_reasoning", "rag", "document_management"]))
        new_tools = list(dict.fromkeys(curr_tools + DOCUMENT_TOOLS))

        if "DOCUMENT SECTION & REPOSITORY ACCESS" not in curr_prompt:
            new_prompt = curr_prompt.strip() + "\n\n" + DOC_DIRECTIVE.strip()
        else:
            new_prompt = curr_prompt

        db.agents.update_one(
            {"_id": a["_id"]},
            {"$set": {
                "systemPrompt": new_prompt,
                "capabilities": new_caps,
                "tools": new_tools
            }}
        )
        print(f"Successfully updated agent '{slug}': {len(new_tools)} tools, {len(new_caps)} capabilities.")

if __name__ == "__main__":
    sync_agents()
