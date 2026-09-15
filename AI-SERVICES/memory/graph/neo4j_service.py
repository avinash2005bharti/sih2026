"""
Neo4j Knowledge Graph Service for Sovereign AI Workbench.
Handles entity/relationship persistence, graph context extraction, and resilient Cypher execution.
Supports both official Neo4j Bolt driver and HTTP transactional fallback.
"""

import os
import base64
import httpx
from typing import Any, Dict, List, Optional
from core.config import settings
from core.logging import logger

try:
    from neo4j import GraphDatabase, Driver
    HAS_NEO4J_LIB = True
except ImportError:
    HAS_NEO4J_LIB = False
    Driver = None


class Neo4jGraphService:
    """Enterprise-grade local Neo4j client for knowledge graph modeling."""

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None
    ):
        self.uri = uri or os.getenv("NEO4J_URI") or getattr(settings, "NEO4J_URI", "bolt://localhost:7687")
        self.http_url = os.getenv("NEO4J_URL") or getattr(settings, "NEO4J_URL", "http://localhost:7474")
        self.username = username or os.getenv("NEO4J_USERNAME") or getattr(settings, "NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD") or getattr(settings, "NEO4J_PASSWORD", "sovereignpass")
        self.database = database or os.getenv("NEO4J_DATABASE") or getattr(settings, "NEO4J_DATABASE", "neo4j")
        
        self._driver: Optional[Any] = None
        self._auth_enabled: Optional[bool] = None
        logger.info(f"[NEO4J] Initialized Neo4jGraphService (URI: {self.uri}, HTTP: {self.http_url})")

    def _get_driver(self) -> Optional[Any]:
        """Lazy-initialize Bolt driver with automatic auth fallback."""
        if not HAS_NEO4J_LIB:
            return None
        if self._driver is not None:
            return self._driver

        uris = [self.uri]
        if "neo4j:7687" in self.uri:
            uris.append("bolt://localhost:7687")
            uris.append("bolt://127.0.0.1:7687")
        elif "localhost" in self.uri:
            uris.append("bolt://127.0.0.1:7687")

        for u in uris:
            # 1. Try with credentials
            if self.password:
                try:
                    drv = GraphDatabase.driver(u, auth=(self.username, self.password), connection_timeout=1.5)
                    drv.verify_connectivity()
                    self._driver = drv
                    self._auth_enabled = True
                    logger.info(f"[NEO4J] Connected via Bolt with authentication to {u}")
                    return self._driver
                except Exception as e:
                    logger.debug(f"[NEO4J] Bolt auth connect failed to {u}: {e}")

            # 2. Try with no auth (e.g. NEO4J_AUTH=none in docker)
            try:
                drv = GraphDatabase.driver(u, auth=None, connection_timeout=1.5)
                drv.verify_connectivity()
                self._driver = drv
                self._auth_enabled = False
                logger.info(f"[NEO4J] Connected via Bolt without authentication to {u}")
                return self._driver
            except Exception as e:
                logger.debug(f"[NEO4J] Bolt unauthenticated connect failed to {u}: {e}")

        return None

    async def execute_cypher(
        self,
        statement: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute Cypher query using Bolt driver if available, falling back to HTTP transactional API.
        """
        driver = self._get_driver()
        if driver:
            try:
                with driver.session(database=self.database) as session:
                    res = session.run(statement, parameters or {})
                    records = [record.data() for record in res]
                    return {"success": True, "results": records}
            except Exception as e:
                logger.debug(f"[NEO4J] Bolt execution warning: {e}. Attempting HTTP fallback...")

        # Fallback to HTTP endpoint
        return await self._execute_http(statement, parameters)

    async def _execute_http(
        self,
        statement: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute Cypher statement via HTTP transactional commit endpoint."""
        urls = [
            f"{self.http_url.rstrip('/')}/db/{self.database}/tx/commit",
            f"http://localhost:7474/db/{self.database}/tx/commit",
            f"http://127.0.0.1:7474/db/{self.database}/tx/commit",
        ]

        payload = {
            "statements": [
                {
                    "statement": statement,
                    "parameters": parameters or {}
                }
            ]
        }

        auth_headers_list = []
        if self.password:
            auth_bytes = f"{self.username}:{self.password}".encode("utf-8")
            b64_auth = base64.b64encode(auth_bytes).decode("utf-8")
            auth_headers_list.append({"Authorization": f"Basic {b64_auth}"})
        auth_headers_list.append({})  # Unauthenticated fallback

        for u in urls:
            for headers in auth_headers_list:
                req_headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    **headers
                }
                try:
                    async with httpx.AsyncClient(timeout=1.5) as client:
                        resp = await client.post(u, json=payload, headers=req_headers)
                        if resp.status_code in [200, 201]:
                            data = resp.json()
                            errors = data.get("errors", [])
                            if errors:
                                logger.debug(f"[NEO4J] HTTP Cypher error: {errors}")
                                continue
                            results = data.get("results", [])
                            formatted = []
                            if results:
                                columns = results[0].get("columns", [])
                                for row in results[0].get("data", []):
                                    formatted.append(dict(zip(columns, row.get("row", []))))
                            return {"success": True, "results": formatted}
                except Exception as e:
                    logger.debug(f"[NEO4J] HTTP connect failed {u}: {e}")

        return {"success": False, "error": "Neo4j unavailable on both Bolt and HTTP"}

    async def health_check(self) -> Dict[str, Any]:
        """Verify Neo4j connectivity and report node and relationship statistics."""
        try:
            res = await self.execute_cypher("MATCH (n) RETURN count(n) AS node_count")
            if res.get("success"):
                nodes = res["results"][0].get("node_count", 0) if res["results"] else 0
                rel_res = await self.execute_cypher("MATCH ()-[r]->() RETURN count(r) AS rel_count")
                rels = rel_res["results"][0].get("rel_count", 0) if rel_res.get("success") and rel_res["results"] else 0
                return {
                    "status": "healthy",
                    "uri": self.uri,
                    "database": self.database,
                    "node_count": nodes,
                    "relationship_count": rels
                }
        except Exception as e:
            logger.debug(f"[NEO4J] Health check error: {e}")

        return {
            "status": "unavailable",
            "uri": self.uri,
            "error": "Failed to connect to Neo4j"
        }

    async def record_memory(
        self,
        memory_id: str,
        user_id: str,
        content: str,
        memory_type: str = "fact",
        conversation_id: Optional[str] = None,
        entities: Optional[List[str]] = None,
        source: str = "conversation"
    ) -> bool:
        """
        Record a Memory node in the knowledge graph, linking it to the User and extracted Entities.
        Schema:
          (:User)-[:HAS_MEMORY]->(:Memory)-[:ABOUT]->(:Entity)
        """
        cypher = """
        MERGE (u:User {id: $user_id})
        MERGE (m:Memory {id: $memory_id})
        SET m.content = $content,
            m.type = $memory_type,
            m.source = $source,
            m.conversation_id = $conversation_id,
            m.updated_at = datetime()
        MERGE (u)-[:HAS_MEMORY]->(m)
        """
        params = {
            "user_id": str(user_id),
            "memory_id": str(memory_id),
            "content": content,
            "memory_type": memory_type,
            "source": source,
            "conversation_id": str(conversation_id or "")
        }

        res = await self.execute_cypher(cypher, params)
        if not res.get("success"):
            return False

        # Link any extracted entities
        if entities:
            for entity in entities:
                ent_name = str(entity).strip()
                if not ent_name or len(ent_name) < 2:
                    continue
                ent_cypher = """
                MATCH (m:Memory {id: $memory_id})
                MERGE (e:Entity {name: $entity_name})
                MERGE (m)-[:ABOUT]->(e)
                """
                await self.execute_cypher(ent_cypher, {
                    "memory_id": str(memory_id),
                    "entity_name": ent_name
                })

        return True

    async def query_related_context(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query graph context related to terms in user query.
        Traverses relationships to find connected facts, entities, and memories.
        """
        q_lower = query.lower()
        is_self_query = any(k in q_lower for k in [
            "my name", "who am i", "who is talking", "about me", "who i am",
            "my profile", "creator", "founder", "my role", "where am i from"
        ])

        words = [w.strip("?,.!;:()[]{}'\"") for w in query.split() if len(w) >= 3]

        if not words and not is_self_query:
            return []

        # If identity query, pull user's key profile memories and entities
        if is_self_query and user_id:
            cypher = """
            MATCH (u:User {id: $user_id})-[:HAS_MEMORY]->(m:Memory)
            OPTIONAL MATCH (m)-[:ABOUT]->(e:Entity)
            OPTIONAL MATCH (e)-[r]-(other)
            RETURN m.content AS memory_content,
                   m.type AS memory_type,
                   e.name AS entity_name,
                   coalesce(type(r), "ABOUT") AS relationship,
                   coalesce(other.name, e.name, "") AS related_target
            LIMIT $limit
            """
            params = {"user_id": str(user_id), "limit": limit}
            res = await self.execute_cypher(cypher, params)
            if res.get("success") and res.get("results"):
                return res.get("results", [])

        # Standard term traversal
        cypher = """
        MATCH (u:User {id: $user_id})-[:HAS_MEMORY]->(m:Memory)
        OPTIONAL MATCH (m)-[:ABOUT]->(e:Entity)
        OPTIONAL MATCH (e)-[r]-(other)
        WHERE any(term IN $terms WHERE toLower(m.content) CONTAINS toLower(term) OR toLower(e.name) CONTAINS toLower(term))
        RETURN m.content AS memory_content,
               m.type AS memory_type,
               e.name AS entity_name,
               type(r) AS relationship,
               coalesce(other.name, other.id, "") AS related_target
        LIMIT $limit
        """
        params = {
            "user_id": str(user_id or "system"),
            "terms": words[:6],
            "limit": limit
        }
        res = await self.execute_cypher(cypher, params)
        if res.get("success"):
            return res.get("results", [])
        return []

    async def record_task_execution(
        self,
        task_id: str,
        task_type: str,
        tool_name: Optional[str] = None,
        document_name: Optional[str] = None
    ) -> bool:
        """Record task execution in graph for provenance tracking."""
        cypher = """
        MERGE (t:Task {id: $task_id})
        SET t.type = $task_type, t.timestamp = datetime()
        """
        params = {"task_id": str(task_id), "task_type": str(task_type)}

        if tool_name:
            cypher += """
            MERGE (tl:Tool {name: $tool_name})
            MERGE (t)-[:USED_TOOL]->(tl)
            """
            params["tool_name"] = str(tool_name)

        if document_name:
            cypher += """
            MERGE (d:Document {name: $doc_name})
            MERGE (t)-[:ACCESSED]->(d)
            """
            params["doc_name"] = str(document_name)

        res = await self.execute_cypher(cypher, params)
        return res.get("success", False)


# Global singleton instance
neo4j_service = Neo4jGraphService()
