"""
Graph Database service for storing agent responses, hallucinations, and relationships.
Implements Neo4j graph database with RAG capabilities for contextual retrieval.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Neo4j driver not installed. Install with: pip install neo4j")

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("Sentence transformers not installed. Install with: pip install sentence-transformers")

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """Base class for graph nodes."""
    id: str
    node_type: str
    properties: Dict[str, Any]
    created_at: datetime


@dataclass
class AgentNode(GraphNode):
    """Agent node in the graph."""
    agent_id: str
    name: str
    version: str
    performance_score: float


@dataclass
class ResponseNode(GraphNode):
    """Response node with embedding for RAG."""
    response_text: str
    embedding: Optional[List[float]]
    hallucination_risk: float
    confidence: float
    processing_time_ms: float


@dataclass
class HallucinationNode(GraphNode):
    """Hallucination pattern node."""
    pattern_type: str
    severity: str
    description: str
    frequency: int


@dataclass
class QueryNode(GraphNode):
    """Query/prompt node."""
    query_text: str
    context: str
    domain: str


@dataclass
class CorrectionNode(GraphNode):
    """Correction/mitigation node."""
    correction_text: str
    validation_score: float
    source: str  # human, ai, automated


class GraphDatabaseService:
    """Neo4j graph database service with RAG capabilities."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 username: str = "neo4j", 
                 password: str = "password"):
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        self.embedding_model = None
        
        # Initialize embedding model for RAG
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded sentence transformer model for embeddings")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")
        
        # Connect to Neo4j
        self.connect()
    
    def connect(self):
        """Connect to Neo4j database."""
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j driver not available. Using mock implementation.")
            return
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("Connected to Neo4j database")
            
            # Initialize schema
            self._initialize_schema()
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            logger.info("Falling back to mock implementation")
            self.driver = None
    
    def _initialize_schema(self):
        """Initialize database schema and constraints."""
        if not self.driver:
            return
        
        constraints_and_indexes = [
            # Unique constraints
            "CREATE CONSTRAINT agent_id_unique IF NOT EXISTS FOR (a:Agent) REQUIRE a.agent_id IS UNIQUE",
            "CREATE CONSTRAINT response_id_unique IF NOT EXISTS FOR (r:Response) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT query_id_unique IF NOT EXISTS FOR (q:Query) REQUIRE q.id IS UNIQUE",
            "CREATE CONSTRAINT hallucination_id_unique IF NOT EXISTS FOR (h:Hallucination) REQUIRE h.id IS UNIQUE",
            "CREATE CONSTRAINT correction_id_unique IF NOT EXISTS FOR (c:Correction) REQUIRE c.id IS UNIQUE",
            
            # Indexes for performance
            "CREATE INDEX response_timestamp IF NOT EXISTS FOR (r:Response) ON (r.timestamp)",
            "CREATE INDEX response_risk IF NOT EXISTS FOR (r:Response) ON (r.hallucination_risk)",
            "CREATE INDEX agent_performance IF NOT EXISTS FOR (a:Agent) ON (a.performance_score)",
            "CREATE INDEX hallucination_severity IF NOT EXISTS FOR (h:Hallucination) ON (h.severity)",
        ]
        
        with self.driver.session() as session:
            for constraint in constraints_and_indexes:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.debug(f"Constraint/index already exists or failed: {e}")
    
    def close(self):
        """Close database connection."""
        if self.driver:
            self.driver.close()
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using sentence transformer."""
        if not self.embedding_model:
            return None
        
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    async def store_agent_response(self, 
                                 agent_id: str,
                                 agent_name: str,
                                 query_text: str,
                                 response_text: str,
                                 hallucination_risk: float,
                                 confidence: float,
                                 processing_time_ms: float,
                                 hallucinated_segments: List[str] = None,
                                 metadata: Dict[str, Any] = None) -> str:
        """Store agent response and relationships in graph database."""
        
        if not self.driver:
            # Mock implementation for when Neo4j is not available
            response_id = f"response_{datetime.utcnow().timestamp()}"
            logger.info(f"Mock: Stored response {response_id} from agent {agent_id}")
            return response_id
        
        response_id = f"response_{datetime.utcnow().timestamp()}"
        query_id = f"query_{hash(query_text) % 1000000}"
        timestamp = datetime.utcnow().isoformat()
        
        # Generate embedding for RAG
        embedding = self.generate_embedding(response_text)
        
        with self.driver.session() as session:
            # Create or update agent node
            session.run("""
                MERGE (a:Agent {agent_id: $agent_id})
                SET a.name = $agent_name,
                    a.last_seen = $timestamp,
                    a.total_responses = COALESCE(a.total_responses, 0) + 1
            """, agent_id=agent_id, agent_name=agent_name, timestamp=timestamp)
            
            # Create query node
            session.run("""
                MERGE (q:Query {id: $query_id})
                SET q.text = $query_text,
                    q.timestamp = $timestamp,
                    q.domain = $domain
            """, query_id=query_id, query_text=query_text, timestamp=timestamp,
                       domain=metadata.get('domain', 'general') if metadata else 'general')
            
            # Create response node with embedding
            session.run("""
                CREATE (r:Response {
                    id: $response_id,
                    text: $response_text,
                    hallucination_risk: $hallucination_risk,
                    confidence: $confidence,
                    processing_time_ms: $processing_time_ms,
                    timestamp: $timestamp,
                    embedding: $embedding,
                    metadata: $metadata_json
                })
            """, response_id=response_id, response_text=response_text,
                       hallucination_risk=hallucination_risk, confidence=confidence,
                       processing_time_ms=processing_time_ms, timestamp=timestamp,
                       embedding=embedding, metadata_json=json.dumps(metadata or {}))
            
            # Create relationships
            session.run("""
                MATCH (a:Agent {agent_id: $agent_id})
                MATCH (r:Response {id: $response_id})
                MATCH (q:Query {id: $query_id})
                CREATE (a)-[:GENERATED]->(r)
                CREATE (r)-[:RESPONDS_TO]->(q)
            """, agent_id=agent_id, response_id=response_id, query_id=query_id)
            
            # Store hallucination patterns if detected
            if hallucination_risk > 0.5 and hallucinated_segments:
                for i, segment in enumerate(hallucinated_segments):
                    hallucination_id = f"hallucination_{response_id}_{i}"
                    session.run("""
                        CREATE (h:Hallucination {
                            id: $hallucination_id,
                            pattern: $segment,
                            severity: $severity,
                            timestamp: $timestamp,
                            response_id: $response_id
                        })
                        WITH h
                        MATCH (r:Response {id: $response_id})
                        CREATE (r)-[:CONTAINS]->(h)
                    """, hallucination_id=hallucination_id, segment=segment,
                           severity='high' if hallucination_risk > 0.8 else 'medium',
                           timestamp=timestamp, response_id=response_id)
        
        logger.info(f"Stored response {response_id} from agent {agent_id} in graph database")
        return response_id
    
    async def find_similar_responses(self, query_text: str, response_text: str, 
                                   limit: int = 5, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find similar responses using RAG for contextual retrieval."""
        
        if not self.driver or not self.embedding_model:
            return []
        
        # Generate embedding for current response
        current_embedding = self.generate_embedding(response_text)
        if not current_embedding:
            return []
        
        similar_responses = []
        
        with self.driver.session() as session:
            # Get all responses with embeddings
            result = session.run("""
                MATCH (r:Response)
                WHERE r.embedding IS NOT NULL
                RETURN r.id as id, r.text as text, r.embedding as embedding,
                       r.hallucination_risk as risk, r.confidence as confidence,
                       r.timestamp as timestamp
                ORDER BY r.timestamp DESC
                LIMIT 1000
            """)
            
            for record in result:
                stored_embedding = record["embedding"]
                if stored_embedding:
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(current_embedding, stored_embedding)
                    
                    if similarity >= similarity_threshold:
                        similar_responses.append({
                            "id": record["id"],
                            "text": record["text"],
                            "similarity": similarity,
                            "hallucination_risk": record["risk"],
                            "confidence": record["confidence"],
                            "timestamp": record["timestamp"]
                        })
        
        # Sort by similarity and return top results
        similar_responses.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_responses[:limit]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    async def get_agent_performance_metrics(self, agent_id: str = None, 
                                          days: int = 30) -> Dict[str, Any]:
        """Get performance metrics for agents."""
        
        if not self.driver:
            # Mock data for when Neo4j is not available
            return {
                "total_responses": 150,
                "avg_hallucination_risk": 0.23,
                "avg_confidence": 0.87,
                "flagged_responses": 12,
                "avg_processing_time": 1250.5,
                "trend": "improving"
            }
        
        with self.driver.session() as session:
            query = """
                MATCH (a:Agent)
                WHERE ($agent_id IS NULL OR a.agent_id = $agent_id)
                MATCH (a)-[:GENERATED]->(r:Response)
                WHERE datetime(r.timestamp) > datetime() - duration({days: $days})
                RETURN 
                    a.agent_id as agent_id,
                    a.name as agent_name,
                    count(r) as total_responses,
                    avg(r.hallucination_risk) as avg_hallucination_risk,
                    avg(r.confidence) as avg_confidence,
                    sum(CASE WHEN r.hallucination_risk > 0.5 THEN 1 ELSE 0 END) as flagged_responses,
                    avg(r.processing_time_ms) as avg_processing_time
                ORDER BY total_responses DESC
            """
            
            result = session.run(query, agent_id=agent_id, days=days)
            
            metrics = []
            for record in result:
                metrics.append({
                    "agent_id": record["agent_id"],
                    "agent_name": record["agent_name"],
                    "total_responses": record["total_responses"],
                    "avg_hallucination_risk": record["avg_hallucination_risk"],
                    "avg_confidence": record["avg_confidence"],
                    "flagged_responses": record["flagged_responses"],
                    "avg_processing_time": record["avg_processing_time"]
                })
            
            return metrics[0] if agent_id and metrics else {"agents": metrics}
    
    async def get_hallucination_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most common hallucination patterns."""
        
        if not self.driver:
            # Mock data
            return [
                {"pattern": "quantum router", "frequency": 15, "severity": "high"},
                {"pattern": "telepathic delivery", "frequency": 12, "severity": "high"},
                {"pattern": "flux capacitor", "frequency": 8, "severity": "medium"},
                {"pattern": "unlimited vacation", "frequency": 6, "severity": "medium"},
                {"pattern": "free Tesla", "frequency": 4, "severity": "low"}
            ]
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (h:Hallucination)
                RETURN h.pattern as pattern, 
                       count(*) as frequency,
                       h.severity as severity
                ORDER BY frequency DESC
                LIMIT $limit
            """, limit=limit)
            
            patterns = []
            for record in result:
                patterns.append({
                    "pattern": record["pattern"],
                    "frequency": record["frequency"],
                    "severity": record["severity"]
                })
            
            return patterns
    
    async def get_time_series_data(self, days: int = 30, 
                                 interval: str = "day") -> List[Dict[str, Any]]:
        """Get time series data for trends and analytics."""
        
        if not self.driver:
            # Mock time series data
            from datetime import timedelta
            base_date = datetime.utcnow() - timedelta(days=days)
            mock_data = []
            
            for i in range(days):
                date = base_date + timedelta(days=i)
                mock_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "total_responses": 45 + (i % 10) * 5,
                    "avg_hallucination_risk": 0.2 + (i % 7) * 0.05,
                    "flagged_responses": 3 + (i % 5),
                    "avg_processing_time": 1200 + (i % 8) * 100
                })
            
            return mock_data
        
        with self.driver.session() as session:
            # Adjust query based on interval
            date_format = "%Y-%m-%d" if interval == "day" else "%Y-%m-%d %H:00:00"
            
            result = session.run(f"""
                MATCH (r:Response)
                WHERE datetime(r.timestamp) > datetime() - duration({{days: $days}})
                WITH date(datetime(r.timestamp)) as date_bucket, r
                RETURN 
                    toString(date_bucket) as date,
                    count(r) as total_responses,
                    avg(r.hallucination_risk) as avg_hallucination_risk,
                    sum(CASE WHEN r.hallucination_risk > 0.5 THEN 1 ELSE 0 END) as flagged_responses,
                    avg(r.processing_time_ms) as avg_processing_time
                ORDER BY date
            """, days=days)
            
            time_series = []
            for record in result:
                time_series.append({
                    "date": record["date"],
                    "total_responses": record["total_responses"],
                    "avg_hallucination_risk": record["avg_hallucination_risk"],
                    "flagged_responses": record["flagged_responses"],
                    "avg_processing_time": record["avg_processing_time"]
                })
            
            return time_series
    
    async def store_correction(self, hallucination_id: str, 
                             correction_text: str, 
                             validation_score: float,
                             source: str = "human") -> str:
        """Store a correction for a hallucination."""
        
        correction_id = f"correction_{datetime.utcnow().timestamp()}"
        timestamp = datetime.utcnow().isoformat()
        
        if not self.driver:
            logger.info(f"Mock: Stored correction {correction_id} for hallucination {hallucination_id}")
            return correction_id
        
        with self.driver.session() as session:
            session.run("""
                CREATE (c:Correction {
                    id: $correction_id,
                    text: $correction_text,
                    validation_score: $validation_score,
                    source: $source,
                    timestamp: $timestamp
                })
                WITH c
                MATCH (h:Hallucination {id: $hallucination_id})
                CREATE (h)-[:CORRECTED_BY]->(c)
            """, correction_id=correction_id, correction_text=correction_text,
                       validation_score=validation_score, source=source,
                       timestamp=timestamp, hallucination_id=hallucination_id)
        
        logger.info(f"Stored correction {correction_id} for hallucination {hallucination_id}")
        return correction_id


# Global graph database instance
_graph_db: Optional[GraphDatabaseService] = None

def get_graph_database() -> GraphDatabaseService:
    """Get or create graph database instance."""
    global _graph_db
    if _graph_db is None:
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        _graph_db = GraphDatabaseService(neo4j_uri, neo4j_username, neo4j_password)
    
    return _graph_db
