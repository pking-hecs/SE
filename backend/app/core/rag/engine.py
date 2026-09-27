import numpy as np
from sentence_transformers import SentenceTransformer
from backend.app.core.config import settings
import logging
from sqlalchemy import text
from backend.app.main import SessionLocal

logger = logging.getLogger(__name__)

class RAGEngine:
    """
    RAG Engine for local financial knowledge base.
    Uses sentence-transformers for embeddings and pgvector for storage.
    """
    def __init__(self):
        # Load local embedding model
        try:
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Embedding model {settings.EMBEDDING_MODEL} loaded.")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.model = None

    def generate_embedding(self, text_str: str):
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
        return self.model.encode(text_str).tolist()

    async def retrieve_context(self, query: str, project_id: int, limit: int = 5):
        """
        Retrieve top-k relevant chunks from pgvector.
        """
        query_embedding = self.generate_embedding(query)

        db = SessionLocal()
        try:
            # Note: In a production pgvector setup, we use the Vector type.
            # Here we cast the embedding list to a string or use pgvector's <=> operator.
            # We join with documents to ensure we only get chunks for the current project.
            sql = text("""
                SELECT c.content
                FROM document_chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE d.project_id = :project_id
                ORDER BY c.embedding <=> :embedding
                LIMIT :limit
            """)

            # Convert embedding list to the format pgvector expects (e.g., '[0.1, 0.2, ...]')
            embedding_str = str(query_embedding)

            result = db.execute(sql, {"project_id": project_id, "embedding": embedding_str, "limit": limit})
            return [row[0] for row in result.all()]
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return []
        finally:
            db.close()

rag_engine = RAGEngine()
