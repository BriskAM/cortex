import os
import chromadb

class ChromaService:
    def __init__(self):
        self.persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
        self.client = chromadb.PersistentClient(path=self.persist_dir)

    def get_or_create_collection(self, name):
        """Create or load a ChromaDB collection using cosine similarity distance metric."""
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )

    def store_embeddings(self, collection_name, ids, embeddings, metadatas, documents):
        """Store chunk documents, embeddings, and metadata in a collection."""
        collection = self.get_or_create_collection(collection_name)
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )

    def query_embeddings(self, collection_name, query_embedding, n_results=6, filter_metadata=None):
        """Query vector database for similar embeddings."""
        collection = self.get_or_create_collection(collection_name)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )
        return results

    def delete_collection(self, name):
        """Delete a collection from ChromaDB database."""
        try:
            self.client.delete_collection(name)
        except Exception:
            pass # Collection might not exist
