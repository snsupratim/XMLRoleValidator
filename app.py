# app.py
import streamlit as st
import os
import tempfile
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Import core logic from src
from src.xml_parser import extract_roles_from_xml
from src.pdf_extractor_rag import RAGPDFExtractor
from src.role_comparer import RoleComparer
from config.config import FUZZY_MATCH_THRESHOLD, PINECONE_API_KEY, PINECONE_INDEX_NAME
from pinecone import Pinecone
import time # For optional Pinecone index deletion wait


def run_comparison(xml_file, pdf_file):
    """
    Handles the core logic for role extraction and comparison
    after files have been uploaded.
    """
    # --- Create temporary files for processing ---
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp_xml:
        tmp_xml.write(xml_file.getvalue())
        xml_filepath = tmp_xml.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        tmp_pdf.write(pdf_file.getvalue())
        pdf_filepath = tmp_pdf.name

    try:
        st.subheader("Processing Initiated")
        st.info("Loading configurations and initializing AI clients...")

        # --- Optional: Clean Pinecone Index for a Fresh Start (especially for free tier) ---
        st.markdown("\n--- **Pinecone Index Management** ---")
        try:
            # Re-initialize Pinecone client just for deletion check if needed
            pc_root = Pinecone(api_key=PINECONE_API_KEY)
            if PINECONE_INDEX_NAME in pc_root.list_indexes().names():
                st.warning(f"Index '{PINECONE_INDEX_NAME}' already exists. Deleting for a fresh run...")
                pc_root.delete_index(PINECONE_INDEX_NAME)
                st.info(f"Index '{PINECONE_INDEX_NAME}' deleted. Waiting a few seconds for full removal...")
                time.sleep(5) # Give Pinecone time to process deletion
                st.success("Proceeding with new index creation.")
            else:
                st.info(f"Index '{PINECONE_INDEX_NAME}' does not exist. It will be created during processing.")
        except Exception as e:
            st.error(f"Error during Pinecone index cleanup: {e}. Please check your Pinecone API key and console.")
            st.warning("Continuing without full index cleanup, which might cause issues.")


        # --- 1. Extract roles from XML ---
        st.subheader("Step 1: Extracting roles from XML")
        with st.spinner("Parsing XML file..."):
            xml_role_xpath = '//role/text()' # Ensure this XPath matches your XML structure
            xml_roles = extract_roles_from_xml(xml_filepath, xml_role_xpath)
            st.write(f"**Extracted XML Roles:** {xml_roles}")
            if not xml_roles:
                st.warning("No roles extracted from XML. Please check XML file and XPath.")

        # --- 2. Initialize RAG PDF Extractor ---
        st.subheader("Step 2: Initializing PDF Extractor and Pinecone")
        with st.spinner("Initializing PDF extractor and Pinecone client. This may take a moment..."):
            pdf_extractor = RAGPDFExtractor()

        # --- 3. Process the PDF and extract roles ---
        pdf_id = "uploaded-document" # A fixed ID for the uploaded PDF
        st.subheader("Step 3: Processing PDF and Extracting Roles via Gemini")
        with st.spinner(f"Clearing previous data for PDF ID: {pdf_id} in Pinecone (if any)..."):
            pdf_extractor.clear_pdf_data(pdf_id)
        
        with st.spinner(f"Processing and indexing PDF: {pdf_file.name}. This involves embedding data..."):
            pdf_extractor.process_pdf(pdf_filepath, pdf_id)
            st.success(f"PDF processed and indexed into Pinecone.")

        with st.spinner("Extracting roles from PDF using Gemini LLM. This may take a moment..."):
            pdf_roles = pdf_extractor.extract_roles_from_pdf(pdf_filepath)
            st.write(f"**Extracted PDF Roles (via RAG):** {pdf_roles}")
            if not pdf_roles:
                st.warning("No roles extracted from PDF. This might indicate issues with PDF content or LLM extraction prompt.")

        # --- 4. Compare roles ---
        st.subheader("Step 4: Comparing Roles")
        comparer = RoleComparer(fuzzy_threshold=FUZZY_MATCH_THRESHOLD)
        is_incorrect, matched_roles, incorrect_pdf_roles = comparer.compare_roles(xml_roles, pdf_roles)

        # --- 5. Generate report ---
        st.subheader("Step 5: Generating Report")
        st.markdown("--- **Role Comparison Report** ---")
        st.write(f"**Total Unique Roles in XML:** {len(xml_roles)}")
        st.write(f"**Total Unique Roles found in PDF:** {len(pdf_roles)}")

        st.markdown("\n--- **Roles Matched (XML to PDF)** ---")
        if matched_roles:
            for role in matched_roles:
                st.write(f"- {role}")
        else:
            st.info("No roles from PDF matched any XML role.")

        st.markdown("\n--- **INCORRECT PDF ROLES (Found in PDF but NOT matching any XML role)** ---")
        if incorrect_pdf_roles:
            st.error("There are roles in the PDF that do NOT match the XML definitions!")
            for role in incorrect_pdf_roles:
                st.write(f"- {role}")
        else:
            st.success("All roles found in the PDF match the XML definitions! (Or no roles were found in PDF).")

        st.markdown("-----------------------------")
        if is_incorrect:
            st.error("CONCLUSION: Roles in the PDF are INCORRECT as there are roles that do not match the XML definitions.")
        else:
            st.success("CONCLUSION: All roles in the PDF are CORRECT according to the XML definitions.")

        st.success("Process Completed!")

    except Exception as e:
        st.error(f"An unexpected error occurred during the process: {e}")
        st.exception(e) # Display full traceback in Streamlit

    finally:
        # --- Clean up temporary files ---
        if os.path.exists(xml_filepath):
            os.remove(xml_filepath)
        if os.path.exists(pdf_filepath):
            os.remove(pdf_filepath)


st.set_page_config(page_title="Role Validator Application", layout="centered")
st.title("📄 Role Validator Application")
st.markdown("Upload your XML file (containing defined roles) and PDF file (containing roles to validate).")

# File Uploaders
uploaded_xml_file = st.file_uploader("Upload XML File (e.g., defined_roles.xml)", type=["xml"])
uploaded_pdf_file = st.file_uploader("Upload PDF File (e.g., document_with_roles.pdf)", type=["pdf"])

if uploaded_xml_file and uploaded_pdf_file:
    st.success("Both files uploaded successfully!")
    if st.button("Start Validation"):
        run_comparison(uploaded_xml_file, uploaded_pdf_file)
else:
    st.info("Please upload both an XML and a PDF file to start the validation process.")