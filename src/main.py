# src/main.py
import os
from src.xml_parser import extract_roles_from_xml
from src.pdf_extractor_rag import RAGPDFExtractor
from src.role_comparer import RoleComparer
from config.config import FUZZY_MATCH_THRESHOLD
from pinecone import Pinecone, PodSpec # Import Pinecone for optional index deletion
from pinecone.exceptions import PineconeApiException, NotFoundException
from config.config import PINECONE_API_KEY, PINECONE_INDEX_NAME
import time # For time.sleep

def main():
    # --- Configuration ---
    # Path to your XML file defining correct roles
    xml_filepath = os.path.join('data', 'xml_data', 'defined_roles.xml')
    # Path to your PDF document to be validated
    pdf_filepath = os.path.join('data', 'pdf_data', 'document_with_roles.pdf')
    # XPath to extract role text from your XML. Adjust as per your XML structure.
    # Example: If XML is <roles><role>Engineer</role></roles>, use '//role/text()'
    # If XML is <employees><employee><title>Manager</title></employee></employees>, use '//employee/title/text()'
    xml_role_xpath = '//role/text()'

    # --- Setup Directories ---
    os.makedirs(os.path.dirname(xml_filepath), exist_ok=True)
    os.makedirs(os.path.dirname(pdf_filepath), exist_ok=True)

    # --- Create Dummy XML File (for initial testing) ---
    # This will create 'data/xml_data/defined_roles.xml' if it doesn't exist.
    # Modify roles here to match your test scenarios.
    print(f"Ensuring dummy XML file exists at: {xml_filepath}")
    dummy_xml_content = """<roles>
    <role>Software Engineer</role>
    <role>Project Manager</role>
    <role>Senior Developer</role>
    <role>QA Tester</role>
    <role>Business Analyst</role>
    <role>Data Scientist</role>
</roles>"""
    with open(xml_filepath, 'w') as f:
        f.write(dummy_xml_content)
    print("Dummy XML file created/updated.")

    # --- Important: Prepare your PDF File ---
    # You MUST manually place a PDF file named 'document_with_roles.pdf'
    # into the 'data/pdf_data/' directory.
    # This PDF should contain text, tables, and potentially images that
    # mention job roles. For testing incorrect roles, include some roles
    # not present in your XML, or misspell some.
    if not os.path.exists(pdf_filepath):
        print(f"\n--- IMPORTANT ---")
        print(f"PDF file not found at: {pdf_filepath}")
        print(f"Please create a PDF document (e.g., using Word/Google Docs and exporting) ")
        print(f"with sample job roles and save it as '{os.path.basename(pdf_filepath)}'")
        print(f"in the '{os.path.dirname(pdf_filepath)}' directory.")
        print(f"Example content for your PDF:")
        print(f"\"Our team comprises a Software Engineer, a Project Manager, and a Sr. Developer.")
        print(f"We are also looking for a Quality Assurance Tester and a Sales Executive.")
        print(f"Table of Staffing: | Role | Count |\\n| Project Managment | 2 |\\n| Data Science | 1 |\"")
        print(f"--- Exiting ---")
        return

    print(f"Using PDF file: {pdf_filepath}")

    # --- Optional: Clean Pinecone Index for a Fresh Start (especially for free tier) ---
    # This block ensures that if an index with the same name exists, it's deleted
    # and recreated. This can be helpful to avoid conflicts or stale data in free tiers.
    print("\n--- Optional: Checking and preparing Pinecone index for a fresh start ---")
    try:
        pc_root = Pinecone(api_key=PINECONE_API_KEY)
        if PINECONE_INDEX_NAME in pc_root.list_indexes().names():
            print(f"Index '{PINECONE_INDEX_NAME}' already exists. Deleting for a fresh run...")
            pc_root.delete_index(PINECONE_INDEX_NAME)
            print(f"Index '{PINECONE_INDEX_NAME}' deleted. Waiting a few seconds for full removal...")
            time.sleep(5) # Give Pinecone time to process deletion
            print("Proceeding with index creation (if not already existing).")
        else:
            print(f"Index '{PINECONE_INDEX_NAME}' does not exist. It will be created shortly.")
    except PineconeApiException as e:
        print(f"Error managing Pinecone index during pre-run cleanup: {e}")
        print("Please check your Pinecone API key and network connection. Continuing without full cleanup.")
    except Exception as e:
        print(f"An unexpected error occurred during Pinecone cleanup: {e}. Continuing.")


    # --- 1. Extract roles from XML ---
    print("\n--- Step 1: Extracting roles from XML ---")
    xml_roles = extract_roles_from_xml(xml_filepath, xml_role_xpath)
    print(f"Extracted XML Roles: {xml_roles}")
    if not xml_roles:
        print("Warning: No roles extracted from XML. Please check XML file and XPath.")

    # --- 2. Initialize RAG PDF Extractor ---
    print("\n--- Step 2: Initializing PDF Extractor and Pinecone ---")
    pdf_extractor = RAGPDFExtractor()

    # --- 3. Process the PDF and extract roles ---
    pdf_id = "your-document-id-001" # A unique identifier for your PDF document
    # Optional: Clear previous data for this PDF in Pinecone.
    # This is less critical now with the optional index deletion above, but good for fine-grained control.
    print(f"Clearing previous data for PDF ID: {pdf_id} in Pinecone (if any)...")
    pdf_extractor.clear_pdf_data(pdf_id)
    print(f"Processing PDF for indexing: {pdf_filepath}")
    pdf_extractor.process_pdf(pdf_filepath, pdf_id)

    print(f"\n--- Step 3: Extracting roles from PDF using Gemini LLM ---")
    pdf_roles = pdf_extractor.extract_roles_from_pdf(pdf_filepath)
    print(f"Extracted PDF Roles (via RAG): {pdf_roles}")
    if not pdf_roles:
        print("Warning: No roles extracted from PDF. This might indicate issues with PDF content or LLM extraction prompt.")

    # --- 4. Compare roles ---
    print("\n--- Step 4: Comparing roles ---")
    comparer = RoleComparer(fuzzy_threshold=FUZZY_MATCH_THRESHOLD)
    is_incorrect, matched_roles, incorrect_pdf_roles = comparer.compare_roles(xml_roles, pdf_roles)

    # --- 5. Generate report ---
    print("\n--- Step 5: Generating Report ---")
    comparer.generate_report(is_incorrect, matched_roles, incorrect_pdf_roles, xml_roles, pdf_roles)

    # # Optional: Demonstrate a general query using RAG (retrieving from Pinecone and using LLM)
    # print("\n--- Optional: Testing a general query on PDF content via RAG ---")
    # general_query = "How many roles do we have in the pdf?"
    # query_response = pdf_extractor.query_pdf_for_roles_from_pinecone(pdf_filepath, general_query)
    # print(f"Query: '{general_query}'")
    # print(f"RAG Response: {query_response}")
    print("\n--- End of Process ---")


if __name__ == "__main__":
    main()