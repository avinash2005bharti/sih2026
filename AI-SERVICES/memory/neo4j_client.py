"""
Compatibility bridge for Neo4jGraphClient.
Delegates to Neo4jGraphService.
"""

from typing import Any, Dict, List, Optional
from memory.graph.neo4j_service import neo4j_service


class Neo4jGraphClient:
    """Compatibility wrapper delegating to Neo4jGraphService."""

    def __init__(self, url: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None):
        self.service = neo4j_service

    async def execute_cypher(self, statement: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.service.execute_cypher(statement, parameters)

    async def record_task_execution(
        self,
        task_id: str,
        task_type: str,
        tool_name: Optional[str] = None,
        document_name: Optional[str] = None
    ) -> bool:
        return await self.service.record_task_execution(task_id, task_type, tool_name, document_name)

    async def query_related_entities(self, entity_name: str) -> List[Dict[str, Any]]:
        cypher = """
        MATCH (e {name: $name})-[r]-(connected)
        RETURN type(r) AS relationship, labels(connected) AS labels, connected.name AS connected_name
        LIMIT 20
        """
        res = await self.service.execute_cypher(cypher, {"name": entity_name})
        results = []
        if res.get("success") and res.get("results"):
            for row in res["results"]:
                results.append({
                    "relationship": row.get("relationship"),
                    "labels": row.get("labels"),
                    "target": row.get("connected_name")
                })
        return results


# Global singleton instance
neo4j_client = Neo4jGraphClient()
