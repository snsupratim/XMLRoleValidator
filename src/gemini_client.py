# src/gemini_client.py
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from config.config import GOOGLE_API_KEY

genai.configure(api_key=GOOGLE_API_KEY)

class GeminiClient:
    def __init__(self, model_name="gemini-1.5-flash"):
        # Configure safety settings for Gemini-pro model
        self.model = genai.GenerativeModel(
            model_name,
            safety_settings=[
                {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_NONE},
                {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_NONE},
                {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_NONE},
                {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_NONE},
            ]
        )
        # No need to instantiate EmbeddingModel directly here, use genai.embed_content directly in the method.
        # self.embedding_model = genai.EmbeddingModel("models/embedding-001") # This line is NOT needed

    def generate_text(self, prompt: str) -> str:
        """Generates text using the Gemini model."""
        try:
            response = self.model.generate_content(prompt)
            if response.candidates:
                return response.text
            else:
                print("Gemini API returned no candidates.")
                return ""
        except Exception as e:
            print(f"Error generating text with Gemini: {e}")
            return ""

    def embed_text(self, text: str) -> list:
        """Generates embeddings for the given text using Google's embedding model."""
        try:
            # Call embed_content directly from the genai module, specifying the model
            response = genai.embed_content(model="models/embedding-001", content=[text])
            if response and 'embedding' in response:
                # Ensure the embedding is a flat list of floats
                # It should already be, but this will enforce it if there's any nesting
                embedding = response['embedding']
                if isinstance(embedding, list) and all(isinstance(x, (float, int)) for x in embedding):
                    return embedding
                elif isinstance(embedding, list) and len(embedding) == 1 and isinstance(embedding[0], list):
                    # If it's a list containing a single list (e.g., [[...]]), flatten it
                    return embedding[0]
                else:
                    print(f"Unexpected embedding format: {type(embedding)} - {embedding}")
                    return []
            else:
                print("Gemini Embedding API returned no embedding.")
                return []
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []