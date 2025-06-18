# src/utils.py
import re
from fuzzywuzzy import fuzz

def normalize_role(role_name: str) -> str:
    """Normalizes a role name for consistent comparison."""
    if not isinstance(role_name, str):
        return ""
    normalized = role_name.lower().strip()
    # Remove non-alphanumeric characters except whitespace
    normalized = re.sub(r'[^\w\s]', '', normalized)
    return normalized

def fuzzy_match(str1: str, str2: str, threshold: int) -> bool:
    """Performs fuzzy matching between two strings."""
    return fuzz.ratio(str1, str2) >= threshold

def chunk_text(text: str, chunk_size: int, overlap: int) -> list:
    """Splits text into chunks with a specified size and overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # Ensure ASCII for embedding model compatibility if needed, otherwise remove .encode/.decode
        segment = text[start:end].encode('ascii', 'ignore').decode('ascii')
        chunks.append(segment)
        if start + chunk_size >= len(text): # Avoid infinite loop if chunk_size - overlap is 0 or less
            break
        start += chunk_size - overlap
    return chunks