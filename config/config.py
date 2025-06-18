# config/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Google Gemini API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Pinecone API Key and Index Name
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "role-comparison-index") # Default name if not set in .env

# Other configurations
PDF_CHUNK_SIZE = int(os.getenv("PDF_CHUNK_SIZE", 1000))
PDF_CHUNK_OVERLAP = int(os.getenv("PDF_CHUNK_OVERLAP", 100))
ROLE_EXTRACTION_PROMPT = os.getenv(
    "ROLE_EXTRACTION_PROMPT",
    "List all the job roles or titles mentioned in the following document. "
    "Provide a comma-separated list of unique roles. If no roles are found, respond with 'None'."
)
FUZZY_MATCH_THRESHOLD = int(os.getenv("FUZZY_MATCH_THRESHOLD", 80))

# --- IMPORTANT ---
# Create a .env file in the ROOT of your project (same level as 'src' and 'config' folders)
# with your actual keys and desired Pinecone index name:
#
# GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE
# PINECONE_API_KEY=YOUR_PINECONE_API_KEY_HERE
# PINECONE_INDEX_NAME=your-pinecone-index-name
#
# Remember to add .env to your .gitignore file to prevent exposing sensitive information.