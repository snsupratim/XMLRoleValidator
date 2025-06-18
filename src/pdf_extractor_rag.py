# src/pdf_extractor_rag.py
import fitz  # PyMuPDF
from src.utils import chunk_text
from src.gemini_client import GeminiClient
from src.pinecone_client import PineconeClient
from config.config import PDF_CHUNK_SIZE, PDF_CHUNK_OVERLAP, ROLE_EXTRACTION_PROMPT
import uuid # For generating unique IDs
from pinecone.exceptions import NotFoundException # Import the specific exception

class RAGPDFExtractor:
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.pinecone_client = PineconeClient()

    def _extract_text_and_tables_from_pdf(self, pdf_path: str) -> str:
        """
        Extracts text content from a PDF file, including tables.
        Handles text and table extraction. For images, OCR might be needed
        as a pre-processing step if they contain relevant text.
        """
        full_text = []
        try:
            pdf_document = fitz.open(pdf_path)
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                # Extract text blocks
                text_blocks = page.get_text("blocks")
                for block in text_blocks:
                    # block[4] is the text content
                    full_text.append(block[4].strip())

                # Extract tables
                tables = page.find_tables()
                for table in tables:
                    table_rows = []
                    for row_data in table.extract():
                        table_rows.append(" | ".join([cell if cell is not None else "" for cell in row_data]))
                    table_str = "\n".join(table_rows)
                    # --- MODIFICATION: More descriptive markers for tables ---
                    full_text.append(f"\n--- DATA TABLE WITH ROLES AND COUNTS ---\n{table_str.strip()}\n--- END OF TABLE DATA ---")
                    # --- END MODIFICATION ---
            pdf_document.close()
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
        
        full_document_text = "\n\n".join(full_text)
        # --- DEBUGGING LINE: UNCOMMENTED ---
        print(f"\n--- DEBUG: Full Extracted PDF Text (including tables) ---\n{full_document_text}\n---------------------------------------------------\n")
        # --- END DEBUG LINE ---
        return full_document_text


    def process_pdf(self, pdf_path: str, pdf_id: str):
        """Processes the PDF: extracts text, chunks, embeds, and upserts to Pinecone."""
        text = self._extract_text_and_tables_from_pdf(pdf_path)
        if not text.strip():
            print(f"No content extracted from {pdf_path}. Skipping indexing.")
            return

        chunks = chunk_text(text, PDF_CHUNK_SIZE, PDF_CHUNK_OVERLAP)
        vectors_to_upsert = []
        for i, chunk in enumerate(chunks):
            embedding = self.gemini_client.embed_text(chunk)
            if embedding:
                # Use a unique ID for each vector
                vector_id = f"{pdf_id}-{uuid.uuid4().hex}"
                vectors_to_upsert.append((vector_id, embedding, {"pdf_id": pdf_id, "chunk_index": i, "content": chunk}))
        
        if vectors_to_upsert:
            self.pinecone_client.upsert_vectors(vectors=vectors_to_upsert)
            print(f"Processed and indexed {len(chunks)} chunks from {pdf_path}")
        else:
            print(f"No embeddings generated for {pdf_path}. Skipping indexing.")

    def extract_roles_from_pdf(self, pdf_path: str) -> list:
        """Extracts roles from the PDF using Gemini LLM."""
        # For role extraction, we directly send the full extracted text (including table markers) to the LLM
        extracted_text = self._extract_text_and_tables_from_pdf(pdf_path)
        if not extracted_text.strip():
            print(f"No content extracted from {pdf_path} for role extraction.")
            return []

        prompt = f"{ROLE_EXTRACTION_PROMPT}\n\nDocument Content:\n{extracted_text}"
        print("Sending prompt to Gemini for role extraction...")
        raw_roles_str = self.gemini_client.generate_text(prompt)

        roles = []
        if raw_roles_str and raw_roles_str.lower() != 'none':
            roles = [role.strip() for role in raw_roles_str.split(',') if role.strip()]
            return list(set(roles))
        elif raw_roles_str.lower() == 'none':
            print("Gemini reported no roles found in the document.")
        else:
            print("Gemini returned empty or unparseable response for roles.")
        return []

    def clear_pdf_data(self, pdf_id: str):
        """Deletes all vectors associated with a specific PDF ID from Pinecone."""
        try:
            self.pinecone_client.index.delete(filter={"pdf_id": {"$eq": pdf_id}})
            print(f"Deleted data for PDF ID: {pdf_id} from Pinecone.")
        except NotFoundException:
            print(f"No existing data found for PDF ID: {pdf_id} in Pinecone. Skipping delete.")
        except Exception as e:
            print(f"An unexpected error occurred while deleting data for PDF ID {pdf_id}: {e}")

    def query_pdf_for_roles_from_pinecone(self, pdf_path: str, query: str) -> str:
        """
        Queries the processed PDF content (via Pinecone) for specific information.
        This demonstrates RAG in action for general queries, not just role extraction.
        """
        query_embedding = self.gemini_client.embed_text(query)
        if not query_embedding:
            return "Could not generate query embedding."

        # --- IMPORTANT: Print raw Pinecone results for debugging ---
        # Increased top_k to ensure more context is retrieved if available
        results = self.pinecone_client.query_vectors(query_embedding, top_k=10) 
        print(f"\n--- DEBUG: Raw Pinecone Query Results (top {len(results.matches)} matches) ---")
        for match in results.matches:
            print(f"  ID: {match.id}, Score: {match.score}, Content (first 100 chars): {match.metadata.get('content', '')[:100]}...")
        print("---------------------------------------------------\n")

        if not results.matches: # Changed to check results.matches directly
            return "No relevant information found in PDF."

        retrieved_contexts = []
        for match in results.matches: # Iterate over results.matches
            if 'metadata' in match and 'content' in match.metadata:
                retrieved_contexts.append(match.metadata['content'])
            else:
                print(f"Warning: Content not found in metadata for vector ID: {match.id}")

        if not retrieved_contexts:
            # This handles cases where matches exist but lack 'content' metadata
            return "No content retrieved from relevant chunks."

        full_context = "\n\n".join(retrieved_contexts)
        
        # --- DEBUGGING LINE: UNCOMMENTED ---
        print("\n--- DEBUG: Context sent to LLM for general query ---")
        print(full_context)
        print("---------------------------------------------------\n")
        # --- END DEBUG LINES ---

        # IMPROVEMENT: Tailor the prompt for table data extraction
        if "table" in query.lower() or "count" in query.lower() or "number of" in query.lower() or "how many" in query.lower():
            prompt = (f"Based on the following document excerpts, specifically focus on any tables or structured lists "
                      f"to answer the question: '{query}'. If exact numbers are provided, use them. "
                      f"If no relevant table or count is found, state that.\n\n"
                      f"Document Excerpts:\n{full_context}\n\nAnswer:")
        else:
            prompt = (f"Based on the following document excerpts, answer the question: '{query}'.\n\n"
                      f"Document Excerpts:\n{full_context}\n\nAnswer:")

        answer = self.gemini_client.generate_text(prompt)
        return answer