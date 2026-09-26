import os

class SimpleRAG:
    """
    A lightweight RAG prototype.
    In a full production system, this would use a Vector DB (like Chroma or Pinecone).
    For this prototype, we use a keyword-based semantic search over local text files.
    """
    def __init__(self, kb_path="knowledge_base"):
        self.kb_path = kb_path

    def retrieve(self, query):
        # Simple keyword-based retrieval from the knowledge base
        relevant_docs = []

        if not os.path.exists(self.kb_path):
            return "Knowledge base not found."

        for filename in os.listdir(self.kb_path):
            if filename.endswith(".txt"):
                with open(os.path.join(self.kb_path, filename), 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Simple heuristic: if any word from the query is in the document, retrieve it
                    # In a real RAG, we would use embeddings and cosine similarity
                    query_words = query.lower().split()
                    if any(word in content.lower() for word in query_words if len(word) > 3):
                        relevant_docs.append(f"Source ({filename}):\n{content}")

        if not relevant_docs:
            return "No specific regulatory grounding found in the knowledge base."

        return "\n\n---\n\n".join(relevant_docs[:2]) # Return top 2 matches
