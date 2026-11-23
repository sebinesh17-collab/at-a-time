"""
Memory Service - Agent memory management with vector search
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4

from ..database import db
from ..config import settings

logger = logging.getLogger(__name__)


class MemoryService:
    def __init__(self):
        pass

    async def initialize(self):
        """Initialize memory service"""
        logger.info("Memory service initialized")

    # ==================== Memory Operations ====================

    async def create_memory(self, memory_data: Dict) -> Dict:
        """Create a new memory entry"""
        memory_id = str(uuid4())
        now = datetime.utcnow()

        # Calculate expiry
        ttl_days = memory_data.get("ttl_days", settings.default_ttl_days)
        expires_at = now + timedelta(days=ttl_days) if ttl_days > 0 else None

        await db.execute("""
            INSERT INTO memories (id, agent_id, project_id, memory_type, content,
                                 embedding, metadata, importance, expires_at,
                                 created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """, memory_id, memory_data.get("agent_id"), memory_data.get("project_id"),
            memory_data.get("memory_type", "general"),
            memory_data.get("content"), memory_data.get("embedding"),
            memory_data.get("metadata", {}), memory_data.get("importance", 5),
            expires_at, now, now)

        return await self.get_memory(memory_id)

    async def get_memory(self, memory_id: str) -> Optional[Dict]:
        """Get memory by ID"""
        row = await db.fetchrow("SELECT * FROM memories WHERE id = $1", memory_id)
        return dict(row) if row else None

    async def update_memory(self, memory_id: str, updates: Dict) -> Optional[Dict]:
        """Update memory"""
        allowed = ["content", "metadata", "importance", "expires_at"]
        set_clauses = []
        params = [memory_id]
        param_idx = 2

        for field in allowed:
            if field in updates:
                set_clauses.append(f"{field} = ${param_idx}")
                params.append(updates[field])
                param_idx += 1

        if not set_clauses:
            return None

        set_clauses.append("updated_at = NOW()")
        query = f"UPDATE memories SET {', '.join(set_clauses)} WHERE id = $1"
        await db.execute(query, *params)
        return await self.get_memory(memory_id)

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory"""
        result = await db.execute("DELETE FROM memories WHERE id = $1", memory_id)
        return result != "DELETE 0"

    async def list_memories(self, agent_id: str = None, project_id: str = None,
                           memory_type: str = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """List memories with filters"""
        query = "SELECT * FROM memories WHERE 1=1"
        params = []
        param_idx = 1

        if agent_id:
            query += f" AND agent_id = ${param_idx}"
            params.append(agent_id)
            param_idx += 1

        if project_id:
            query += f" AND project_id = ${param_idx}"
            params.append(project_id)
            param_idx += 1

        if memory_type:
            query += f" AND memory_type = ${param_idx}"
            params.append(memory_type)
            param_idx += 1

        # Exclude expired
        query += " AND (expires_at IS NULL OR expires_at > NOW())"

        query += f" ORDER BY importance DESC, created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        rows = await db.fetch(query, *params)
        return [dict(row) for row in rows]

    # ==================== Vector Search ====================

    async def search_memories(self, query_embedding: List[float], agent_id: str = None,
                             project_id: str = None, memory_type: str = None,
                             limit: int = 10, threshold: float = 0.7) -> List[Dict]:
        """Search memories by vector similarity (using pgvector)"""
        # This requires pgvector extension
        # For now, use a simple text search fallback
        return await self.search_memories_text("", agent_id, project_id, memory_type, limit)

    async def search_memories_text(self, query: str, agent_id: str = None,
                                   project_id: str = None, memory_type: str = None,
                                   limit: int = 10) -> List[Dict]:
        """Search memories by text"""
        sql = """
            SELECT *, ts_rank_cd(to_tsvector('english', content), plainto_tsquery('english', $1)) as rank
            FROM memories
            WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $1)
        """
        params = [query]
        param_idx = 2

        if agent_id:
            sql += f" AND agent_id = ${param_idx}"
            params.append(agent_id)
            param_idx += 1

        if project_id:
            sql += f" AND project_id = ${param_idx}"
            params.append(project_id)
            param_idx += 1

        if memory_type:
            sql += f" AND memory_type = ${param_idx}"
            params.append(memory_type)
            param_idx += 1

        sql += " AND (expires_at IS NULL OR expires_at > NOW())"
        sql += f" ORDER BY rank DESC, importance DESC LIMIT ${param_idx}"
        params.append(limit)

        rows = await db.fetch(sql, *params)
        return [dict(row) for row in rows]

    # ==================== Conversation Memory ====================

    async def add_conversation_message(self, conversation_id: str, message_data: Dict) -> Dict:
        """Add a message to a conversation"""
        message_id = str(uuid4())
        now = datetime.utcnow()

        await db.execute("""
            INSERT INTO conversation_messages (id, conversation_id, role, content,
                                              metadata, tokens, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, message_id, conversation_id, message_data["role"],
            message_data["content"], message_data.get("metadata", {}),
            message_data.get("tokens", 0), now)

        return await self.get_conversation_message(message_id)

    async def get_conversation_message(self, message_id: str) -> Optional[Dict]:
        """Get conversation message by ID"""
        row = await db.fetchrow("SELECT * FROM conversation_messages WHERE id = $1", message_id)
        return dict(row) if row else None

    async def get_conversation_history(self, conversation_id: str, limit: int = 100) -> List[Dict]:
        """Get conversation history"""
        rows = await db.fetch("""
            SELECT * FROM conversation_messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
            LIMIT $2
        """, conversation_id, limit)
        return [dict(row) for row in rows]

    async def create_conversation(self, conversation_data: Dict) -> Dict:
        """Create a new conversation"""
        conversation_id = str(uuid4())
        now = datetime.utcnow()

        await db.execute("""
            INSERT INTO conversations (id, agent_id, project_id, title, metadata,
                                      created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, conversation_id, conversation_data.get("agent_id"),
            conversation_data.get("project_id"), conversation_data.get("title"),
            conversation_data.get("metadata", {}), now, now)

        return await self.get_conversation(conversation_id)

    async def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation by ID"""
        row = await db.fetchrow("SELECT * FROM conversations WHERE id = $1", conversation_id)
        return dict(row) if row else None

    async def list_conversations(self, agent_id: str = None, project_id: str = None,
                                limit: int = 50, offset: int = 0) -> List[Dict]:
        """List conversations"""
        query = "SELECT * FROM conversations WHERE 1=1"
        params = []
        param_idx = 1

        if agent_id:
            query += f" AND agent_id = ${param_idx}"
            params.append(agent_id)
            param_idx += 1

        if project_id:
            query += f" AND project_id = ${param_idx}"
            params.append(project_id)
            param_idx += 1

        query += f" ORDER BY updated_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        rows = await db.fetch(query, *params)
        return [dict(row) for row in rows]

    # ==================== Knowledge Base ====================

    async def add_knowledge(self, knowledge_data: Dict) -> Dict:
        """Add knowledge entry"""
        knowledge_id = str(uuid4())
        now = datetime.utcnow()

        await db.execute("""
            INSERT INTO knowledge_base (id, project_id, title, content, source,
                                       embedding, metadata, tags, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, knowledge_id, knowledge_data.get("project_id"),
            knowledge_data["title"], knowledge_data["content"],
            knowledge_data.get("source"), knowledge_data.get("embedding"),
            knowledge_data.get("metadata", {}), knowledge_data.get("tags", []),
            now, now)

        return await self.get_knowledge(knowledge_id)

    async def get_knowledge(self, knowledge_id: str) -> Optional[Dict]:
        """Get knowledge by ID"""
        row = await db.fetchrow("SELECT * FROM knowledge_base WHERE id = $1", knowledge_id)
        return dict(row) if row else None

    async def search_knowledge(self, query: str, project_id: str = None,
                              tags: List[str] = None, limit: int = 10) -> List[Dict]:
        """Search knowledge base"""
        sql = """
            SELECT *, ts_rank_cd(to_tsvector('english', content), plainto_tsquery('english', $1)) as rank
            FROM knowledge_base
            WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $1)
        """
        params = [query]
        param_idx = 2

        if project_id:
            sql += f" AND project_id = ${param_idx}"
            params.append(project_id)
            param_idx += 1

        if tags:
            sql += f" AND tags && ${param_idx}"
            params.append(tags)
            param_idx += 1

        sql += f" ORDER BY rank DESC LIMIT ${param_idx}"
        params.append(limit)

        rows = await db.fetch(sql, *params)
        return [dict(row) for row in rows]

    # ==================== Agent State ====================

    async def save_agent_state(self, agent_id: str, state_data: Dict) -> Dict:
        """Save agent state"""
        now = datetime.utcnow()

        await db.execute("""
            INSERT INTO agent_states (id, agent_id, state_data, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (agent_id) DO UPDATE SET
                state_data = EXCLUDED.state_data,
                updated_at = EXCLUDED.updated_at
        """, str(uuid4()), agent_id, state_data, now, now)

        return await self.get_agent_state(agent_id)

    async def get_agent_state(self, agent_id: str) -> Optional[Dict]:
        """Get agent state"""
        row = await db.fetchrow("SELECT * FROM agent_states WHERE agent_id = $1", agent_id)
        return dict(row) if row else None

    async def delete_agent_state(self, agent_id: str) -> bool:
        """Delete agent state"""
        result = await db.execute("DELETE FROM agent_states WHERE agent_id = $1", agent_id)
        return result != "DELETE 0"


memory_service = MemoryService()