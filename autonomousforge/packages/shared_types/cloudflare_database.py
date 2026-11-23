"""
Cloudflare-aware database abstraction for AUTONOMOUSFORGE
Supports PostgreSQL (asyncpg), Cloudflare D1, and Hyperdrive with automatic detection
"""
import os
import asyncio
from typing import Optional, Dict, Any, List, AsyncGenerator, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass
import logging

from .cloudflare_config import get_cloudflare_config, CloudflareConfig

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConnection:
    """Unified database connection interface"""
    type: str  # postgresql, d1, hyperdrive
    pool: Any = None
    client: Any = None


class CloudflareDatabase:
    """
    Database abstraction that automatically configures for:
    - PostgreSQL (asyncpg) - local or via Cloudflare Tunnel
    - Cloudflare D1 (SQLite-compatible) - via Workers binding
    - Hyperdrive - PostgreSQL connection pooling via Cloudflare
    """

    def __init__(self, config: Optional[CloudflareConfig] = None):
        self.config = config or get_cloudflare_config()
        self._connection: Optional[DatabaseConnection] = None
        self._initialized = False

    async def initialize(self) -> "CloudflareDatabase":
        """Initialize database connection based on environment"""
        if self._initialized:
            return self

        db_config = self.config.database_config
        db_type = db_config.get("type", "postgresql")

        logger.info(f"Initializing database: type={db_type}")

        if db_type == "d1":
            await self._init_d1(db_config)
        elif db_type == "hyperdrive":
            await self._init_hyperdrive(db_config)
        else:
            await self._init_postgresql(db_config)

        self._initialized = True
        return self

    async def _init_d1(self, db_config: Dict[str, Any]):
        """Initialize Cloudflare D1 database connection"""
        try:
            # In Cloudflare Workers, D1 is accessed via binding
            # For Python, we use the d1-py library or HTTP API
            import httpx

            database_id = db_config.get("database_id")
            account_id = os.getenv("CF_ACCOUNT_ID")
            api_token = os.getenv("CF_API_TOKEN")

            if not all([database_id, account_id, api_token]):
                raise ValueError("D1 requires CF_ACCOUNT_ID, CF_API_TOKEN, and D1_DATABASE_ID")

            self._connection = DatabaseConnection(
                type="d1",
                client=httpx.AsyncClient(
                    base_url=f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}",
                    headers={
                        "Authorization": f"Bearer {api_token}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                ),
            )
            logger.info("D1 database connection initialized")

        except ImportError:
            logger.warning("httpx not available for D1, falling back to PostgreSQL")
            await self._init_postgresql({
                "url": os.getenv("DATABASE_URL", "postgresql://forge:forge_secure_password@localhost:5432/autonomousforge")
            })

    async def _init_hyperdrive(self, db_config: Dict[str, Any]):
        """Initialize Hyperdrive connection (uses standard PostgreSQL protocol)"""
        # Hyperdrive exposes a standard PostgreSQL connection string
        connection_string = db_config.get("url") or os.getenv("HYPERDRIVE_CONNECTION_STRING")

        if not connection_string:
            raise ValueError("Hyperdrive requires HYPERDRIVE_CONNECTION_STRING")

        await self._init_postgresql({"url": connection_string})

    async def _init_postgresql(self, db_config: Dict[str, Any]):
        """Initialize PostgreSQL connection pool"""
        try:
            import asyncpg

            database_url = db_config.get("url")
            if not database_url:
                raise ValueError("PostgreSQL requires DATABASE_URL")

            pool_size = db_config.get("pool_size", 20)
            max_overflow = db_config.get("max_overflow", 10)

            pool = await asyncpg.create_pool(
                database_url,
                min_size=5,
                max_size=pool_size + max_overflow,
                command_timeout=60,
            )

            self._connection = DatabaseConnection(
                type="postgresql",
                pool=pool,
            )
            logger.info(f"PostgreSQL pool initialized: {pool_size} connections")

        except ImportError:
            logger.error("asyncpg not installed. Install with: pip install asyncpg")
            raise

    @asynccontextmanager
    async def acquire(self):
        """Acquire a database connection"""
        if not self._initialized:
            await self.initialize()

        if self._connection.type == "d1":
            # For D1, return the HTTP client
            yield self._connection.client
        else:
            # For PostgreSQL/Hyperdrive, acquire from pool
            async with self._connection.pool.acquire() as conn:
                yield conn

    async def execute(self, query: str, *args) -> str:
        """Execute a query (INSERT, UPDATE, DELETE)"""
        async with self.acquire() as conn:
            if self._connection.type == "d1":
                # D1 uses HTTP API
                response = await conn.post("/query", json={"sql": query, "params": list(args)})
                response.raise_for_status()
                return response.json()
            else:
                return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch multiple rows"""
        async with self.acquire() as conn:
            if self._connection.type == "d1":
                response = await conn.post("/query", json={"sql": query, "params": list(args)})
                response.raise_for_status()
                data = response.json()
                return data.get("result", [{}])[0].get("results", [])
            else:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch a single row"""
        async with self.acquire() as conn:
            if self._connection.type == "d1":
                response = await conn.post("/query", json={"sql": query, "params": list(args)})
                response.raise_for_status()
                data = response.json()
                results = data.get("result", [{}])[0].get("results", [])
                return results[0] if results else None
            else:
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value"""
        async with self.acquire() as conn:
            if self._connection.type == "d1":
                response = await conn.post("/query", json={"sql": query, "params": list(args)})
                response.raise_for_status()
                data = response.json()
                results = data.get("result", [{}])[0].get("results", [])
                if results:
                    return list(results[0].values())[0]
                return None
            else:
                return await conn.fetchval(query, *args)

    async def executemany(self, query: str, args_list: List[tuple]) -> None:
        """Execute multiple parameter sets"""
        async with self.acquire() as conn:
            if self._connection.type == "d1":
                # Batch via multiple requests
                for args in args_list:
                    await self.execute(query, *args)
            else:
                await conn.executemany(query, args_list)

    @asynccontextmanager
    async def transaction(self):
        """Transaction context manager"""
        if self._connection.type == "d1":
            # D1 doesn't support transactions via HTTP API
            # Use batch statements instead
            yield D1Batch(self)
        else:
            async with self._connection.pool.acquire() as conn:
                async with conn.transaction():
                    yield conn

    async def close(self):
        """Close database connections"""
        if self._connection:
            if self._connection.type == "d1" and self._connection.client:
                await self._connection.client.aclose()
            elif self._connection.pool:
                await self._connection.pool.close()
            self._connection = None
            self._initialized = False

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information for debugging"""
        if not self._connection:
            return {"status": "not_initialized"}

        info = {
            "type": self._connection.type,
            "initialized": self._initialized,
        }

        if self._connection.type == "postgresql" and self._connection.pool:
            info["pool_size"] = self._connection.pool.get_size()
            info["pool_idle"] = self._connection.pool.get_idle_size()

        return info


class D1Batch:
    """Batch operations for D1 (simulates transactions)"""

    def __init__(self, db: CloudflareDatabase):
        self.db = db
        self.statements = []

    def execute(self, query: str, *args):
        self.statements.append({"sql": query, "params": list(args)})

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and self.statements:
            # Execute batch
            client = self.db._connection.client
            response = await client.post("/batch", json=self.statements)
            response.raise_for_status()


# Convenience functions
async def get_database() -> CloudflareDatabase:
    """Get initialized database instance"""
    db = CloudflareDatabase()
    await db.initialize()
    return db


@asynccontextmanager
async def database_connection() -> AsyncGenerator[CloudflareDatabase, None]:
    """Context manager for database connection"""
    db = await get_database()
    try:
        yield db
    finally:
        await db.close()


# Integration with existing database.py pattern
class Database:
    """Drop-in replacement for existing database.py"""

    def __init__(self, database_url: Optional[str] = None):
        self._cf_db = CloudflareDatabase()
        self._database_url = database_url

    async def connect(self):
        await self._cf_db.initialize()

    async def disconnect(self):
        await self._cf_db.close()

    async def execute(self, query: str, *args):
        return await self._cf_db.execute(query, *args)

    async def fetch(self, query: str, *args):
        return await self._cf_db.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        return await self._cf_db.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        return await self._cf_db.fetchval(query, *args)

    @property
    def pool(self):
        """Backward compatibility - returns the underlying pool"""
        if self._cf_db._connection and self._cf_db._connection.type == "postgresql":
            return self._cf_db._connection.pool
        return None


# Global database instance
_database: Optional[Database] = None


async def get_db() -> Database:
    """Get global database instance"""
    global _database
    if _database is None:
        _database = Database()
        await _database.connect()
    return _database


async def init_db(database_url: Optional[str] = None) -> Database:
    """Initialize global database"""
    global _database
    _database = Database(database_url)
    await _database.connect()
    return _database


async def close_db():
    """Close global database"""
    global _database
    if _database:
        await _database.disconnect()
        _database = None