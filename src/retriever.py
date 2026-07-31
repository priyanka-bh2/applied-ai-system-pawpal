"""
RAG Retriever Module for PawPal+
Retrieves breed-specific care guidelines using vector similarity search.
"""

import json
import os
from typing import List, Dict
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

class CareGuidelineRetriever:
    """Retrieves pet care guidelines using RAG (Retrieval-Augmented Generation)"""
    
    def __init__(self, knowledge_base_path: str = "data/knowledge_base/breed_guidelines.json"):
        """Initialize retriever with embeddings and knowledge base"""
        self.knowledge_base_path = knowledge_base_path
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.documents = self._load_knowledge_base()
        self.vectorstore = self._build_vectorstore()
    
    def _load_knowledge_base(self) -> List[Document]:
        """Load breed guidelines from JSON and convert to Document objects"""
        if not os.path.exists(self.knowledge_base_path):
            raise FileNotFoundError(f"Knowledge base not found: {self.knowledge_base_path}")
        
        with open(self.knowledge_base_path, 'r') as f:
            data = json.load(f)
        
        documents = []
        for breed_info in data['breeds']:
            content = f"""
Breed: {breed_info['breed']}
Exercise Requirements: {breed_info['exercise']}
Diet: {breed_info['diet']}
Grooming: {breed_info['grooming']}
Health Concerns: {breed_info['health_concerns']}
Lifespan: {breed_info['lifespan']}
Special Notes: {breed_info['special_notes']}
"""
            doc = Document(
                page_content=content,
                metadata={"breed": breed_info['breed'], "source": "breed_guidelines"}
            )
            documents.append(doc)
        
        return documents
    
    def _build_vectorstore(self) -> FAISS:
        """Build FAISS vector store from documents"""
        return FAISS.from_documents(self.documents, self.embeddings)
    
    def retrieve(self, query: str, k: int = 2) -> List[str]:
        """
        Retrieve top-k most relevant care guidelines for a query
        
        Args:
            query: Natural language query (e.g., "Golden Retriever exercise needs")
            k: Number of results to retrieve (default 2)
        
        Returns:
            List of relevant care guideline texts
        """
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            return [doc.page_content for doc in docs]
        except Exception as e:
            print(f"Retrieval error: {e}")
            return []
    
    def get_breed_info(self, breed_name: str) -> Dict:
        """Get specific breed information by name"""
        query = f"{breed_name} breed care guidelines"
        results = self.retrieve(query, k=1)
        return results[0] if results else "Breed information not found"