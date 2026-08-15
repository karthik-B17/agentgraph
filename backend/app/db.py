"""
db.py
-----
Sets up ONE shared Neo4j driver instance (used for talking to CognoDB,
since CognoDB speaks the same Bolt protocol Neo4j uses).
"""

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
from contextlib import contextmanager

from app.config import COGNODB_URI, COGNODB_USER, COGNODB_PASSWORD, COGNODB_DATABASE

driver = GraphDatabase.driver(
    COGNODB_URI,
    auth=(COGNODB_USER, COGNODB_PASSWORD),
    connection_timeout=15,          # fail fast instead of hanging
    max_connection_lifetime=300,    # recycle connections proactively
)


def verify_connection() -> bool:
    """Call this once on startup to confirm CognoDB is reachable."""
    try:
        driver.verify_connectivity()
        return True
    except (ServiceUnavailable, AuthError) as e:
        print(f"[db] Could not connect to CognoDB: {e}")
        return False


@contextmanager
def get_session():
    """
    Usage:
        with get_session() as session:
            result = session.run(query, param1=value1)
    """
    session = driver.session(database=COGNODB_DATABASE)
    try:
        yield session
    except ServiceUnavailable as e:
        raise ConnectionError(f"CognoDB is unreachable: {e}") from e
    finally:
        session.close()


def close_driver():
    """Call this on app shutdown to release connections cleanly."""
    driver.close()