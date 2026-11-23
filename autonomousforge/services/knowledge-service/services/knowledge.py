"""
Knowledge Service - Document management and RAG
"""
import logging
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from ..database import db
from ..config import settings

logger = logging.getLogger(__name__)


class KnowledgeService:
    def __init__(self):
        pass

    async def initialize(self):
        """Initialize knowledge service"""
        logger.info("Knowledge service initialized")

    # ==================== Document Operations ====================

    async def create_document(self, document_data: Dict) -> Dict:
        """Create a new document"""
        document_id = str(uuid4())
        now = datetime.utcnow()

        content = document_data.get("content", "")
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Check for duplicate
        existing = await db.fetchrow("SELECT id FROM documents WHERE content_hash = $1", content_hash)
        if existing:
            return await self.get_document(existing["id"])

        await db.execute("""
            INSERT INTO documents (id, project_id, title, content, content_hash, source,
                                  mime_type, metadata, tags, embedding, chunk_count,
                                  created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """, document_id, document_data.get("project_id"), document_data["title"],
            content, content_hash, document_data.get("source"),
            document_data.get("mime_type", "text/plain"),
            document_data.get("metadata", {}), document_data.get("tags", []),
            document_data.get("embedding"), 0, now, now)

        # Auto-chunk if content is large
        if len(content) > settings.chunk_size:
            await self._chunk_document(document_id, content)

        return await self.get_document(document_id)

    async def _chunk_document(self, document_id: str, content: str):
        """Chunk document for RAG"""
        chunk_size = settings.chunk_size
        overlap = settings.chunk_overlap

        chunks = []
        for i in range(0, len(content), chunk_size - overlap):
            chunk_content = content[i:i + chunk_size]
            if len(chunk_content) < 100:  # Skip very small chunks
                continue
            chunks.append(chunk_content)

        for idx, chunk_content in enumerate(chunks):
            chunk_id = str(uuid4())
            await db.execute("""
                INSERT INTO document_chunks (id, document_id, chunk_index, content,
                                            embedding, token_count, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, chunk_id, document_id, idx, chunk_content, None, len(chunk_content), datetime.utcnow())

        # Update chunk count
        await db.execute(
            "UPDATE documents SET chunk_count = $1, updated_at = NOW() WHERE id = $2",
            len(chunks), document_id
        )

    async def get_document(self, document_id: str) -> Optional[Dict]:
        """Get document by ID"""
        row = await db.fetchrow("SELECT * FROM documents WHERE id = $1", document_id)
        return dict(row) if row else None

    async def get_document_with_chunks(self, document_id: str) -> Optional[Dict]:
        """Get document with its chunks"""
        doc = await self.get_document(document_id)
        if not doc:
            return None

        chunks = await db.fetch("""
            SELECT * FROM document_chunks WHERE document_id = $1 ORDER BY chunk_index
        """, document_id)
        doc["chunks"] = [dict(row) for row in chunks]
        return doc

    async def update_document(self, document_id: str, updates: Dict) -> Optional[Dict]:
        """Update document"""
        allowed = ["title", "metadata", "tags", "source"]
        set_clauses = []
        params = [document_id]
        param_idx = 2

        for field in allowed:
            if field in updates:
                set_clauses.append(f"{field} = ${param_idx}")
                params.append(updates[field])
                param_idx += 1

        if "content" in updates:
            content = updates["content"]
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            set_clauses.append(f"content = ${param_idx}")
            params.append(content)
            param_idx += 1
            set_clauses.append(f"content_hash = ${param_idx}")
            params.append(content_hash)
            param_idx += 1

            # Re-chunk
            await db.execute("DELETE FROM document_chunks WHERE document_id = $1", document_id)
            await self._chunk_document(document_id, content)

        if not set_clauses:
            return None

        set_clauses.append("updated_at = NOW()")
        query = f"UPDATE documents SET {', '.join(set_clauses)} WHERE id = $1"
        await db.execute(query, *params)
        return await self.get_document(document_id)

    async def delete_document(self, document_id: str) -> bool:
        """Delete document"""
        result = await db.execute("DELETE FROM documents WHERE id = $1", document_id)
        return result != "DELETE 0"

    async def list_documents(self, project_id: str = None, tags: List[str] = None,
                            limit: int = 100, offset: int = 0) -> List[Dict]:
        """List documents"""
        query = "SELECT * FROM documents WHERE 1=1"
        params = []
        param_idx = 1

        if project_id:
            query += f" AND project_id = ${param_idx}"
            params.append(project_id)
            param_idx += 1

        if tags:
            query += f" AND tags && ${param_idx}"
            params.append(tags)
            param_idx += 1

        query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        rows = await db.fetch(query, *params)
        return [dict(row) for row in rows]

    # ==================== Search ====================

    async def search_documents(self, query: str, project_id: str = None,
                              tags: List[str] = None, limit: int = 10) -> List[Dict]:
        """Search documents using full-text search"""
        sql = """
            SELECT *, ts_rank_cd(to_tsvector('english', content), plainto_tsquery('english', $1)) as rank
            FROM documents
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

    async def search_chunks(self, query: str, project_id: str = None,
                           document_id: str = None, limit: int = 10) -> List[Dict]:
        """Search document chunks"""
        sql = """
            SELECT dc.*, d.title as document_title, d.project_id
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE to_tsvector('english', dc.content) @@ plainto_tsquery('english', $1)
        """
        params = [query]
        param_idx = 2

        if project_id:
            sql += f" AND d.project_id = ${param_idx}"
            params.append(project_id)
            param_idx += 1

        if document_id:
            sql += f" AND dc.document_id = ${param_idx}"
            params.append(document_id)
            param_idx += 1

        sql += f" ORDER BY ts_rank_cd(to_tsvector('english', dc.content), plainto_tsquery('english', $1)) DESC LIMIT ${param_idx}"
        params.append(limit)

        rows = await db.fetch(sql, *params)
        return [dict(row) for row in rows]

    async def semantic_search(self, query_embedding: List[float], project_id: str = None,
                             limit: int = 10, threshold: float = 0.7) -> List[Dict]:
        """Semantic search using vector similarity (requires pgvector)"""
        # Placeholder for pgvector implementation
        # Would use: SELECT * FROM document_chunks WHERE embedding <=> $1 < $2
        return await self.search_chunks("", project_id, None, limit)

    # ==================== Collections ====================

    async def create_collection(self, collection_data: Dict) -> Dict:
        """Create a knowledge collection"""
        collection_id = str(uuid4())
        now = datetime.utcnow()

        await db.execute("""
            INSERT INTO knowledge_collections (id, project_id, name, description,
                                              metadata, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, collection_id, collection_data.get("project_id"),
            collection_data["name"], collection_data.get("description"),
            collection_data.get("metadata", {}), now, now)

        return await self.get_collection(collection_id)

    async def get_collection(self, collection_id: str) -> Optional[Dict]:
        """Get collection by ID"""
        row = await db.fetchrow("SELECT * FROM knowledge_collections WHERE id = $1", collection_id)
        return dict(row) if row else None

    async def list_collections(self, project_id: str = None) -> List[Dict]:
        """List collections"""
        query = "SELECT * FROM knowledge_collections WHERE 1=1"
        params = []
        param_idx = 1

        if project_id:
            query += f" AND project_id = ${param_idx}"
            params.append(project_id)
            param_idx += 1

        query += " ORDER BY created_at DESC"
        rows = await db.fetch(query, *params)
        return [dict(row) for row in rows]

    async def add_document_to_collection(self, collection_id: str, document_id: str) -> bool:
        """Add document to collection"""
        result = await db.execute("""
            INSERT INTO collection_documents (collection_id, document_id)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
        """, collection_id, document_id)
        return result != "INSERT 0"

    async def remove_document_from_collection(self, collection_id: str, document_id: str) -> bool:
        """Remove document from collection"""
        result = await db.execute("""
            DELETE FROM collection_documents WHERE collection_id = $1 AND document_id = $2
        """, collection_id, document_id)
        return result != "DELETE 0"

    async def get_collection_documents(self, collection_id: str) -> List[Dict]:
        """Get documents in a collection"""
        rows = await db.fetch("""
            SELECT d.* FROM documents d
            JOIN collection_documents cd ON cd.document_id = d.id
            WHERE cd.collection_id = $1
            ORDER BY d.created_at DESC
        """, collection_id)
        return [dict(row) for row in rows]

    # ==================== RAG Pipeline ====================

    async def retrieve_context(self, query: str, project_id: str = None,
                              limit: int = 5, use_semantic: bool = False) -> List[Dict]:
        """Retrieve relevant context for RAG"""
        if use_semantic:
            # Would use embeddings
            return await self.search_chunks(query, project_id, None, limit)
        else:
            return await self.search_chunks(query, project_id, None, limit)

    async def generate_answer(self, query: str, context: List[Dict],
                             model_id: str = None) -> Dict:
        """Generate answer using retrieved context (calls model gateway)"""
        # This would call the model gateway
        # For now, return context as answer
        context_text = "\n\n".join([c["content"] for c in context])
        return {
            "query": query,
            "answer": f"Based on {len(context)} retrieved documents: {context_text[:500]}...",
            "sources": [{"document_id": c["document_id"], "chunk_index": c["chunk_index"]} for c in context],
            "model": model_id or "default"
        }


knowledge_service = KnowledgeService()