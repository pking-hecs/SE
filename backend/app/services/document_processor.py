import logging
import pymupdf
import docx
import os
from backend.app.core.config import settings
from backend.app.core.security.guard import security_guard
from backend.app.core.rag.engine import rag_engine
from backend.app.main import SessionLocal
from backend.app.models.schema import Document, DocumentChunk

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Handles ingestion of PDFs, DOCX, and TXT files.
    """
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR

    def extract_text(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        text = ""

        if ext == ".pdf":
            doc = pymupdf.open(file_path)
            for page in doc:
                text += page.get_text()
        elif ext == ".docx":
            doc = docx.Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs])
        elif ext == ".txt" or ext == ".md":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

        return text

    async def process_and_store(self, file_path: str, project_id: int):
        """
        Full pipeline: Extract -> Mask -> Chunk -> Embed -> Store.
        """
        # 1. Extract
        raw_text = self.extract_text(file_path)

        # 2. Mask PII
        safe_text = security_guard.mask_pii(raw_text)

        # 3. Chunking (Simple fixed-size for now)
        # In production, we'd use recursive character splitting
        chunks = [safe_text[i:i+1000] for i in range(0, len(safe_text), 800)]

        # 4. Embed and Store
        db = SessionLocal()
        try:
            # First, create a Document record
            doc_name = os.path.basename(file_path)
            new_doc = Document(
                name=doc_name,
                project_id=project_id,
                file_path=file_path,
                doc_type="REGULATION" # Default; could be inferred from filename or user input
            )
            db.add(new_doc)
            db.commit()
            db.refresh(new_doc)

            for chunk in chunks:
                embedding = rag_engine.generate_embedding(chunk)
                # Store as a string representation for the simple schema
                # pgvector usually handles this via specialized types, but for this demo
                # we match the Text column in schema.py
                chunk_obj = DocumentChunk(
                    document_id=new_doc.id,
                    content=chunk,
                    embedding=str(embedding)
                )
                db.add(chunk_obj)

            db.commit()
            logger.info(f"Processed document {file_path} into {len(chunks)} chunks for Project {project_id}.")
            return True
        except Exception as e:
            logger.error(f"Failed to store document chunks: {e}")
            db.rollback()
            return False
        finally:
            db.close()

document_processor = DocumentProcessor()
