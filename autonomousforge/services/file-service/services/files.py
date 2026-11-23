"""
File Service - File storage and management
"""
import logging
import os
import shutil
import hashlib
import mimetypes
from datetime import datetime
from typing import Optional, List, Dict, Any, BinaryIO
from uuid import uuid4
from pathlib import Path

from ..database import db
from ..config import settings

logger = logging.getLogger(__name__)


class FileService:
    def __init__(self):
        self.storage_path = Path(settings.storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Initialize file service"""
        logger.info(f"File service initialized with storage: {self.storage_path}")

    def _get_file_path(self, file_id: str) -> Path:
        """Get physical file path for a file ID"""
        # Use first 2 chars as subdirectory for better filesystem performance
        subdir = file_id[:2]
        dir_path = self.storage_path / subdir
        dir_path.mkdir(exist_ok=True)
        return dir_path / file_id

    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    # ==================== File Operations ====================

    async def upload_file(self, file_data: BinaryIO, filename: str,
                          content_type: str = None, metadata: Dict = None,
                          project_id: str = None, owner_id: str = None) -> Dict:
        """Upload a file"""
        file_id = str(uuid4())
        now = datetime.utcnow()

        # Detect content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or "application/octet-stream"

        # Save to temporary location first
        temp_path = self.storage_path / f".tmp_{file_id}"
        try:
            with open(temp_path, 'wb') as f:
                shutil.copyfileobj(file_data, f)

            # Check file size
            file_size = temp_path.stat().st_size
            if file_size > settings.max_file_size:
                temp_path.unlink()
                raise ValueError(f"File size exceeds maximum allowed: {settings.max_file_size}")

            # Calculate hash
            file_hash = self._calculate_hash(temp_path)

            # Check for duplicate
            existing = await db.fetchrow("SELECT id FROM files WHERE hash = $1", file_hash)
            if existing:
                temp_path.unlink()
                return await self.get_file(existing["id"])

            # Move to permanent location
            final_path = self._get_file_path(file_id)
            temp_path.rename(final_path)

            # Store metadata in database
            await db.execute("""
                INSERT INTO files (id, filename, content_type, size, hash, storage_path,
                                  metadata, project_id, owner_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, file_id, filename, content_type, file_size, file_hash,
                str(final_path.relative_to(self.storage_path)),
                metadata or {}, project_id, owner_id, now, now)

            return await self.get_file(file_id)

        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise

    async def get_file(self, file_id: str) -> Optional[Dict]:
        """Get file metadata"""
        row = await db.fetchrow("SELECT * FROM files WHERE id = $1", file_id)
        return dict(row) if row else None

    async def get_file_content(self, file_id: str) -> Optional[bytes]:
        """Get file content"""
        file_meta = await self.get_file(file_id)
        if not file_meta:
            return None

        file_path = self.storage_path / file_meta["storage_path"]
        if not file_path.exists():
            return None

        with open(file_path, 'rb') as f:
            return f.read()

    async def download_file(self, file_id: str) -> Optional[tuple]:
        """Download file - returns (content, filename, content_type)"""
        file_meta = await self.get_file(file_id)
        if not file_meta:
            return None

        file_path = self.storage_path / file_meta["storage_path"]
        if not file_path.exists():
            return None

        with open(file_path, 'rb') as f:
            content = f.read()

        return content, file_meta["filename"], file_meta["content_type"]

    async def list_files(self, project_id: str = None, owner_id: str = None,
                         limit: int = 100, offset: int = 0) -> List[Dict]:
        """List files with filters"""
        query = "SELECT * FROM files WHERE 1=1"
        params = []
        param_idx = 1

        if project_id:
            query += f" AND project_id = ${param_idx}"
            params.append(project_id)
            param_idx += 1

        if owner_id:
            query += f" AND owner_id = ${param_idx}"
            params.append(owner_id)
            param_idx += 1

        query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        rows = await db.fetch(query, *params)
        return [dict(row) for row in rows]

    async def update_file(self, file_id: str, updates: Dict) -> Optional[Dict]:
        """Update file metadata"""
        allowed = ["filename", "metadata"]
        set_clauses = []
        params = [file_id]
        param_idx = 2

        for field in allowed:
            if field in updates:
                set_clauses.append(f"{field} = ${param_idx}")
                params.append(updates[field])
                param_idx += 1

        if not set_clauses:
            return None

        set_clauses.append("updated_at = NOW()")
        query = f"UPDATE files SET {', '.join(set_clauses)} WHERE id = $1"
        await db.execute(query, *params)
        return await self.get_file(file_id)

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file"""
        file_meta = await self.get_file(file_id)
        if not file_meta:
            return False

        # Delete physical file
        file_path = self.storage_path / file_meta["storage_path"]
        if file_path.exists():
            file_path.unlink()

        # Delete from database
        result = await db.execute("DELETE FROM files WHERE id = $1", file_id)
        return result != "DELETE 0"

    async def search_files(self, query: str, project_id: str = None,
                           limit: int = 50) -> List[Dict]:
        """Search files by filename or metadata"""
        sql = """
            SELECT * FROM files
            WHERE filename ILIKE $1
        """
        params = [f"%{query}%"]

        if project_id:
            sql += " AND project_id = $2"
            params.append(project_id)

        sql += " ORDER BY created_at DESC LIMIT $3"
        params.append(limit)

        rows = await db.fetch(sql, *params)
        return [dict(row) for row in rows]

    # ==================== Directory Operations ====================

    async def create_directory(self, dir_data: Dict) -> Dict:
        """Create a virtual directory"""
        dir_id = str(uuid4())
        now = datetime.utcnow()

        await db.execute("""
            INSERT INTO directories (id, name, parent_id, path, project_id, owner_id,
                                    created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, dir_id, dir_data["name"], dir_data.get("parent_id"),
            dir_data.get("path"), dir_data.get("project_id"),
            dir_data.get("owner_id"), now, now)

        return await self.get_directory(dir_id)

    async def get_directory(self, dir_id: str) -> Optional[Dict]:
        """Get directory by ID"""
        row = await db.fetchrow("SELECT * FROM directories WHERE id = $1", dir_id)
        return dict(row) if row else None

    async def list_directories(self, parent_id: str = None, project_id: str = None) -> List[Dict]:
        """List directories"""
        query = "SELECT * FROM directories WHERE 1=1"
        params = []
        param_idx = 1

        if parent_id:
            query += f" AND parent_id = ${param_idx}"
            params.append(parent_id)
            param_idx += 1
        else:
            query += " AND parent_id IS NULL"

        if project_id:
            query += f" AND project_id = ${param_idx}"
            params.append(project_id)
            param_idx += 1

        query += " ORDER BY name"
        rows = await db.fetch(query, *params)
        return [dict(row) for row in rows]

    async def delete_directory(self, dir_id: str, recursive: bool = False) -> bool:
        """Delete a directory"""
        if not recursive:
            # Check if empty
            children = await db.fetchrow("SELECT 1 FROM directories WHERE parent_id = $1", dir_id)
            files = await db.fetchrow("SELECT 1 FROM files WHERE directory_id = $1", dir_id)
            if children or files:
                return False

        result = await db.execute("DELETE FROM directories WHERE id = $1", dir_id)
        return result != "DELETE 0"

    # ==================== Project File Tree ====================

    async def get_project_file_tree(self, project_id: str) -> Dict:
        """Get complete file tree for a project"""
        # Get directories
        dirs = await db.fetch("""
            SELECT * FROM directories WHERE project_id = $1 ORDER BY path
        """, project_id)

        # Get files
        files = await db.fetch("""
            SELECT * FROM files WHERE project_id = $1 ORDER BY filename
        """, project_id)

        # Build tree
        dirs_by_id = {row["id"]: dict(row) for row in dirs}
        for d in dirs_by_id.values():
            d["children"] = []
            d["files"] = []

        root_dirs = []
        for d in dirs_by_id.values():
            parent_id = d.get("parent_id")
            if parent_id and parent_id in dirs_by_id:
                dirs_by_id[parent_id]["children"].append(d)
            else:
                root_dirs.append(d)

        # Add files to directories
        for f in files:
            f_dict = dict(f)
            dir_id = f_dict.get("directory_id")
            if dir_id and dir_id in dirs_by_id:
                dirs_by_id[dir_id]["files"].append(f_dict)
            else:
                # Files at root
                pass

        return {
            "project_id": project_id,
            "directories": root_dirs,
            "root_files": [dict(f) for f in files if not f.get("directory_id")]
        }


file_service = FileService()