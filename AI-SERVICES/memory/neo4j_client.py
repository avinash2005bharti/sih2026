"""
Neo4j Knowledge Graph Client for Sovereign AI Workbench.
Connects to Neo4j via HTTP transactional endpoint to store and query
User, Conversation, Document, Task, Tool, and Entity relationships.
"""

import os
import base64
import httpx
from typing import Any, Dict, List, Optional
from core.logging import logger

NEO4J_URL = os.getenv("NEO4J_URL", "http://neo4j:7474")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "sovereignpass")


class Neo4jGraphClient:
    """Client for querying and updating the sovereign Neo4j knowledge graph."""

    def __init__(
        self,
        url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.url = (url or NEO4J_URL).rstrip("/")
        # Fallback to localhost if outside docker
        self.username = username or NEO4J_USER
        self.password = password or NEO4J_PASSWORD
        auth_bytes = f"{self.username}:{self.password}".encode("utf-8")
        self.headers = {
            "Authorization": f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def execute_cypher(self, statement: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a Cypher statement via Neo4j HTTP API."""
        endpoint = f"{self.url}/db/neo4j/tx/commit"
        payload = {
            "statements": [
                {
                    "statement": statement,
                    "parameters": parameters or {}
                }
            ]
        }

        # Try configured URL first, then fallback to localhost:7474
        urls = [endpoint]
        if "neo4j:7474" in endpoint:
            urls.append("http://localhost:7474/db/neo4j/tx/commit")

        for u in urls:
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(u, json=payload, headers=self.headers)
                    if resp.status_code in [200, 201]:
                        data = resp.json()
                        errors = data.get("errors", [])
                        if errors:
                            logger.error(f"[NEO4J] Cypher error: {errors}")
                            return {"success": False, "errors": errors}
                        return {"success": True, "results": data.get("results", [])}
            except Exception as e:
                logger.debug(f"[NEO4J] Connection failed to {u}: {e}")

        return {"success": False, "error": "Could not connect to Neo4j graph database"}

    async def record_task_execution(
        self,
        task_id: str,
        task_type: str,
        tool_name: Optional[str] = None,
        document_name: Optional[str] = None
    ) -> bool:
        """Create or update a Task node and link it to tools or documents."""
        cypher = """
        MERGE (t:Task {id: $task_id})
        SET t.type = $task_type, t.timestamp = datetime()
        """
        params = {"task_id": task_id, "task_type": task_type}

        if tool_name:
            cypher += """
            MERGE (tl:Tool {name: $tool_name})
            MERGE (t)-[:USED_TOOL]->(tl)
            """
            params["tool_name"] = tool_name

        if document_name:
            cypher += """
            MERGE (d:Document {name: $doc_name})
            MERGE (t)-[:ACCESSED]->(d)
            """
            params["doc_name"] = document_name

        res = await self.execute_cypher(cypher, params)
        return res.get("success", False)

    async def query_related_entities(self, entity_name: str) -> List[Dict[str, Any]]:
        """Find nodes connected to a given entity."""
        cypher = """
        MATCH (e {name: $name})-[r]-(connected)
        RETURN type(r) AS relationship, labels(connected) AS labels, connected.name AS connected_name
        LIMIT 20
        """
        res = await self.execute_cypher(cypher, {"name": entity_name})
        results = []
        if res.get("success") and res.get("results"):
            for row in res["results"][0].get("data", []):
                results.append({
                    "relationship": row["row"][0],
                    "labels": row["row"][1],
                    "target": row["row"][2]
                })
        return results


# Global singleton instance
neo4j_client = Neo4jGraphClient()
