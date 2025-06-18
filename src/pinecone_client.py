# src/pinecone_client.py
from pinecone import Pinecone, Index, ServerlessSpec # Added ServerlessSpec
from pinecone.exceptions import PineconeApiException # Import for error handling
from config.config import PINECONE_API_KEY, PINECONE_INDEX_NAME
import time # Import time for waiting for index to be ready

class PineconeClient:
    def __init__(self, index_name=PINECONE_INDEX_NAME, dimension=768): # Gemini embedding dimension is 768
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index_name = index_name
        self.dimension = dimension
        self.index: Index = self._get_or_create_index()

    def _get_or_create_index(self):
        # Check if the index exists
        try:
            existing_indexes = self.pc.list_indexes().names()
        except PineconeApiException as e:
            print(f"Error listing Pinecone indexes: {e}")
            print("Please check your Pinecone API key and network connection.")
            raise # Re-raise to stop execution if API connection fails

        if self.index_name not in existing_indexes:
            print(f"Creating Pinecone index: {self.index_name}")
            try:
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine", # Using cosine as recommended for Google Embeddings
                    spec=ServerlessSpec(cloud="aws", region="us-east-1") # CORRECTED for free tier
                )
                print(f"Index '{self.index_name}' created. Waiting for it to be ready...")
                # Wait for the index to be initialized
                while not self.pc.describe_index(self.index_name).status['ready']:
                    time.sleep(1) # Wait 1 second before checking again
                print(f"Index '{self.index_name}' is ready.")
            except PineconeApiException as e:
                print(f"Error creating Pinecone index '{self.index_name}': {e}")
                print("This might be due to free-tier limits, an invalid API key, or a region issue.")
                raise # Re-raise the exception to stop execution
        else:
            print(f"Pinecone index '{self.index_name}' already exists.")
            # Ensure it's ready if it exists (useful if a previous run crashed before it was ready)
            try:
                if not self.pc.describe_index(self.index_name).status['ready']:
                    print(f"Index '{self.index_name}' is not yet ready. Waiting...")
                    while not self.pc.describe_index(self.index_name).status['ready']:
                        time.sleep(1)
                    print(f"Index '{self.index_name}' is now ready.")
            except PineconeApiException as e:
                print(f"Error describing Pinecone index '{self.index_name}': {e}")
                print("Please check your Pinecone index status in the console.")
                raise # Re-raise if we can't even describe the index

        return self.pc.Index(self.index_name)

    def upsert_vectors(self, vectors: list):
        """Upserts vectors to Pinecone."""
        if not vectors:
            print("No vectors to upsert.")
            return
        try:
            self.index.upsert(vectors=vectors)
            print(f"Upserted {len(vectors)} vectors to Pinecone index '{self.index_name}'.")
        except PineconeApiException as e:
            print(f"Error upserting vectors to Pinecone: {e}")
            # Often, upsert errors are due to index not being ready or malformed vectors
            print("Please ensure the index is ready and vector dimensions/format are correct.")
        except Exception as e:
            print(f"An unexpected error occurred during upsert: {e}")


    def query_vectors(self, query_embedding: list, top_k: int = 3) -> list:
        """Queries Pinecone for similar vectors."""
        try:
            results = self.index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
            return results.matches
        except PineconeApiException as e:
            print(f"Error querying Pinecone: {e}")
            print("Please check your Pinecone API key, index status, and query parameters.")
            return []
        except Exception as e:
            print(f"An unexpected error occurred during query: {e}")
            return []

    def delete_all_vectors(self):
        """Deletes all vectors from the index."""
        try:
            # Note: This deletes ALL vectors in the index, regardless of namespace.
            # If you only wanted to delete for a specific pdf_id, that would be done
            # via a filter, as implemented in pdf_extractor_rag.py's clear_pdf_data.
            self.index.delete(delete_all=True)
            print(f"All vectors deleted from index: {self.index_name}")
        except PineconeApiException as e:
            print(f"Error deleting all vectors from Pinecone: {e}")
            print("This can happen if the index is not found or other API issues.")
        except Exception as e:
            print(f"An unexpected error occurred during full index delete: {e}")