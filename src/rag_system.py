"""
RAG (Retrieval-Augmented Generation) System for Consciousness Research Papers

This module provides a ChromaDB-based RAG system for storing and querying
100+ consciousness research papers, providing therapists with research-backed
insights during sessions.

Architecture:
- ChromaDB for vector storage and similarity search
- Sentence-transformers for embeddings (all-MiniLM-L6-v2)
- PDF ingestion pipeline
- Query interface for real-time research retrieval

Author: Agent 27 - RAG System Builder
"""

import os
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("ChromaDB not available. Install with: pip install chromadb")

logger = logging.getLogger(__name__)


class RAGSystem:
    """
    RAG System for consciousness research papers.

    Features:
    - Vector storage with ChromaDB
    - Semantic search over research papers
    - Metadata filtering (author, year, paper type)
    - Sub-2 second query performance
    """

    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize RAG system with ChromaDB.

        Args:
            persist_directory: Path to persist ChromaDB data
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB not installed. Run: pip install chromadb")

        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Get or create collection for consciousness research
        self.collection = self.client.get_or_create_collection(
            name="consciousness_research",
            metadata={
                "description": "Research papers on consciousness, IIT, GWT, EEG, and therapeutic applications",
                "created_at": datetime.now().isoformat(),
                "hnsw:space": "cosine"  # Use cosine similarity
            }
        )

        logger.info(f"RAG System initialized with {self.collection.count()} papers")

    def ingest_paper(
        self,
        paper_text: str,
        metadata: Dict[str, Any],
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> int:
        """
        Add research paper to vector store with chunking.

        Args:
            paper_text: Full text of the research paper
            metadata: Paper metadata (title, author, year, etc.)
            chunk_size: Size of text chunks for embedding
            chunk_overlap: Overlap between chunks for context

        Returns:
            Number of chunks created
        """
        # Validate required metadata
        required_fields = ['paper_id', 'title', 'author']
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Missing required metadata field: {field}")

        # Chunk the paper text for better retrieval
        chunks = self._chunk_text(paper_text, chunk_size, chunk_overlap)

        # Create IDs and metadata for each chunk
        chunk_ids = [f"{metadata['paper_id']}_chunk_{i}" for i in range(len(chunks))]
        chunk_metadata = [
            {**metadata, 'chunk_index': i, 'total_chunks': len(chunks)}
            for i in range(len(chunks))
        ]

        # Add to collection
        self.collection.add(
            documents=chunks,
            metadatas=chunk_metadata,
            ids=chunk_ids
        )

        logger.info(f"Ingested paper '{metadata['title']}' as {len(chunks)} chunks")
        return len(chunks)

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve relevant papers using semantic search.

        Args:
            query_text: Query string
            n_results: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {'year': '2016'})

        Returns:
            Dictionary with 'documents', 'metadatas', 'distances'
        """
        query_start = datetime.now()

        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=filter_metadata
        )

        query_time = (datetime.now() - query_start).total_seconds()
        logger.info(f"Query completed in {query_time:.3f}s, retrieved {len(results['documents'][0])} results")

        return {
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'distances': results['distances'][0] if results['distances'] else [],
            'query_time': query_time
        }

    def get_research_context(
        self,
        question: str,
        n_results: int = 3,
        include_citations: bool = True
    ) -> str:
        """
        Get research-backed answer context for therapeutic questions.

        Args:
            question: Therapeutic question
            n_results: Number of research papers to include
            include_citations: Whether to include citation information

        Returns:
            Formatted research context string
        """
        results = self.query(question, n_results=n_results)

        if not results['documents']:
            return "No relevant research found."

        context_parts = []
        for i, (doc, meta, distance) in enumerate(
            zip(results['documents'], results['metadatas'], results['distances']), 1
        ):
            citation = ""
            if include_citations:
                author = meta.get('author', 'Unknown')
                year = meta.get('year', 'N/A')
                title = meta.get('title', 'Untitled')
                citation = f"[{i}] {author} ({year}). {title}\n"

            # Truncate long documents
            doc_excerpt = doc[:500] + "..." if len(doc) > 500 else doc
            relevance = f"(Relevance: {1 - distance:.2f})"

            context_parts.append(f"{citation}{doc_excerpt} {relevance}\n")

        return "\n".join(context_parts)

    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific paper by ID.

        Args:
            paper_id: Paper identifier

        Returns:
            Paper data or None if not found
        """
        results = self.collection.get(
            ids=[f"{paper_id}_chunk_0"],  # Get first chunk
        )

        if results['documents']:
            return {
                'document': results['documents'][0],
                'metadata': results['metadatas'][0]
            }
        return None

    def list_papers(self, limit: int = 100) -> List[Dict[str, str]]:
        """
        List all papers in the collection.

        Args:
            limit: Maximum number of papers to return

        Returns:
            List of paper metadata
        """
        # Get all documents
        all_docs = self.collection.get(
            limit=limit,
            include=['metadatas']
        )

        # Deduplicate by paper_id (only show first chunk of each paper)
        seen_papers = set()
        papers = []

        for meta in all_docs['metadatas']:
            paper_id = meta.get('paper_id')
            if paper_id and paper_id not in seen_papers:
                seen_papers.add(paper_id)
                papers.append({
                    'paper_id': paper_id,
                    'title': meta.get('title', 'Untitled'),
                    'author': meta.get('author', 'Unknown'),
                    'year': meta.get('year', 'N/A'),
                    'category': meta.get('category', 'General')
                })

        return papers

    def get_stats(self) -> Dict[str, Any]:
        """
        Get RAG system statistics.

        Returns:
            Dictionary with system statistics
        """
        total_chunks = self.collection.count()
        papers = self.list_papers()

        # Count by category
        categories = {}
        for paper in papers:
            cat = paper.get('category', 'General')
            categories[cat] = categories.get(cat, 0) + 1

        return {
            'total_papers': len(papers),
            'total_chunks': total_chunks,
            'avg_chunks_per_paper': total_chunks / len(papers) if papers else 0,
            'papers_by_category': categories,
            'persist_directory': self.persist_directory
        }

    @staticmethod
    def _chunk_text(
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[str]:
        """
        Split text into overlapping chunks for better retrieval.

        Args:
            text: Full text to chunk
            chunk_size: Target size of each chunk
            overlap: Number of characters to overlap (must be < chunk_size)

        Returns:
            List of text chunks

        Raises:
            ValueError: If overlap >= chunk_size
        """
        # Validation: Prevent infinite loop
        if overlap >= chunk_size:
            raise ValueError(
                f"overlap ({overlap}) must be less than chunk_size ({chunk_size}). "
                f"Recommended: overlap <= chunk_size / 2"
            )

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size

            # Try to break at sentence boundaries
            if end < text_len:
                # Look for sentence end (., !, ?)
                for punct in ['. ', '! ', '? ']:
                    last_punct = text[start:end].rfind(punct)
                    if last_punct != -1:
                        end = start + last_punct + 1
                        break

            chunks.append(text[start:end].strip())

            # Ensure forward progress even with sentence boundary adjustment
            next_start = end - overlap
            if next_start <= start:
                next_start = start + 1  # Force at least 1 char forward
            start = next_start

        return chunks

    def delete_paper(self, paper_id: str) -> int:
        """
        Delete a paper and all its chunks.

        Args:
            paper_id: Paper identifier

        Returns:
            Number of chunks deleted
        """
        # Find all chunk IDs for this paper
        all_docs = self.collection.get()
        chunk_ids_to_delete = [
            doc_id for doc_id in all_docs['ids']
            if doc_id.startswith(f"{paper_id}_chunk_")
        ]

        if chunk_ids_to_delete:
            self.collection.delete(ids=chunk_ids_to_delete)
            logger.info(f"Deleted paper '{paper_id}' ({len(chunk_ids_to_delete)} chunks)")

        return len(chunk_ids_to_delete)

    def reset_collection(self):
        """
        Delete all papers from the collection.
        WARNING: This cannot be undone!
        """
        self.client.delete_collection(name="consciousness_research")
        self.collection = self.client.get_or_create_collection(
            name="consciousness_research",
            metadata={
                "description": "Research papers on consciousness, IIT, GWT, EEG",
                "created_at": datetime.now().isoformat()
            }
        )
        logger.warning("Collection reset - all papers deleted")


def get_research_context(question: str, persist_directory: str = "./chroma_db") -> str:
    """
    Convenience function to get research context for a question.

    Args:
        question: Therapeutic question
        persist_directory: Path to ChromaDB data

    Returns:
        Formatted research context
    """
    rag = RAGSystem(persist_directory=persist_directory)
    return rag.get_research_context(question)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    rag = RAGSystem()

    # Demo: Ingest a test paper
    test_paper = """
    Gamma oscillations in the 30-80 Hz range are strongly associated with
    conscious awareness and information integration. Studies show that high
    gamma power indicates increased consciousness levels, while decreased
    gamma is associated with loss of consciousness during anesthesia.

    The integrated information theory (IIT) proposes that consciousness
    corresponds to integrated information, measured as Phi. Higher Phi values
    indicate more integrated neural networks and higher consciousness levels.
    """

    metadata = {
        'paper_id': 'demo_2024_gamma',
        'title': 'Gamma Oscillations and Consciousness',
        'author': 'Demo Author',
        'year': '2024',
        'category': 'EEG'
    }

    try:
        rag.ingest_paper(test_paper, metadata)

        # Demo query
        question = "What does high gamma power indicate about consciousness?"
        context = rag.get_research_context(question)

        print("\n" + "="*60)
        print("RESEARCH CONTEXT DEMO")
        print("="*60)
        print(f"\nQuestion: {question}\n")
        print(f"Research Context:\n{context}")

        # Show stats
        stats = rag.get_stats()
        print("\n" + "="*60)
        print("RAG SYSTEM STATS")
        print("="*60)
        for key, value in stats.items():
            print(f"{key}: {value}")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
