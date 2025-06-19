# 🤖 AI Role Validator: XML to PDF Job Role Comparison

![YouTube Thumbnail](XMLRoleValidator.png)

> 🚀 A smart tool to compare structured job role definitions (from XML) with roles found in unstructured PDF job descriptions using AI + RAG + fuzzy logic.

---

## 🚀 Overview

The **AI Role Validator** is an intelligent Python application designed to automate and streamline the tedious process of validating job roles.

It compares a definitive list of roles, specified in a structured **XML file**, against job roles identified within **unstructured PDF documents**. By leveraging **Generative AI (Google Gemini)**, **Retrieval-Augmented Generation (RAG)**, and **fuzzy string matching**, it ensures consistency, accuracy, and highlights discrepancies—saving hours of manual effort.

---

## ✨ Features

✅ **XML Role Extraction**
Parses XML files to extract the master list of defined job roles.

✅ **PDF Content Extraction**
Extracts text and tables from PDFs using `PyMuPDF`.

✅ **LLM-Powered Role Extraction**
Uses **Google Gemini AI** to extract roles from complex and unstructured text.

✅ **RAG-Based Enhancement**
Uses **Pinecone** to index and retrieve contextual PDF chunks for accurate AI role extraction.

✅ **Fuzzy Matching**
Handles typos, abbreviations, and formatting inconsistencies using advanced string matching.

✅ **Validation Report**
Categorizes roles as:

- ✔️ Direct / Fuzzy Matches
- ❌ Incorrect / Unmatched Roles

✅ **Configurable Matching Thresholds**
Tune the similarity score sensitivity.

---

## 🧠 How Fuzzy Matching Works

### 1️⃣ Levenshtein Distance – `fuzz.ratio()`

Used to catch **typos** and **minor word-level errors**.

> **Example:**
> XML: `Tester`
> PDF: `Teater`
> → Edit distance = 1 substitution
> → Similarity ≈ **83.33%**

### 2️⃣ Ratcliff-Obershelp – `fuzz.partial_ratio()`

Used to catch **abbreviations** or **substring matches**.

> **Example:**
> XML: `Software Engineer`
> PDF: `Software Eng.`
> → Partial ratio = **100%**
> (as it's a near-perfect subset)

The intelligent combination of both methods ensures robust matching, even across formatting variations and abbreviations.

---

## 🛠️ Technologies Used

- **Python 3.9+**
- **Google Gemini API**
- **Pinecone Vector DB**
- **PyMuPDF (fitz)**
- **thefuzz (fuzzywuzzy)**
- **lxml**
- **langchain-text-splitters**
- **python-dotenv**

---

## ⚙️ Setup and Installation

### 🔹 Prerequisites

- Python 3.9+
- Google Gemini API Key
- Pinecone API Key & Environment

### 🔹 1. Clone the Repository

```bash
git clone https://github.com/snsupratim/XMLRoleValidator.git
cd XMLRoleValidator
```

### 🔹 2. Create and Activate Virtual Environment

```bash
python -m venv myenv
```

- **On Windows:**

  ```bash
  .\myenv\Scripts\activate
  ```

- **On macOS/Linux:**

  ```bash
  source myenv/bin/activate
  ```

### 🔹 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 🔹 4. Setup Environment Variables

Create a `.env` file in the root directory:

```dotenv
GEMINI_API_KEY="your_gemini_api_key_here"
PINECONE_API_KEY="your_pinecone_api_key_here"
PINECONE_ENVIRONMENT="your_pinecone_env_here" # e.g., gcp-starter
```

✅ **Note:** `.env` is already excluded in `.gitignore`.

---

## 🏃 How to Run Locally

### ✅ Step-by-Step

1. Place your **XML role definitions** in:

   ```
   data/xml_data/defined_roles.xml
   ```

2. Place your **PDF documents** in:

   ```
   data/pdf_data/document_with_roles.pdf
   ```

3. Run the application:

```bash
python -m src.main
```

or,

```bash
streamlit run app.py
```

4. The tool will:

   - Extract roles from XML
   - Parse PDF content
   - Generate embeddings via Gemini
   - Perform RAG-based role extraction
   - Fuzzy match against XML roles
   - Display a validation report in the terminal

---

## 📂 Project Structure

```
xmlRoleValidator/
├── config/
│       └── config.py
├── data/
│   ├── pdf_data/
│   │   └── document_with_roles.pdf
│   └── xml_data/
│       └── defined_roles.xml
├── src/
│   ├── main.py
│   │── gemini_client.py
│   │── pinecone_client.py
│   ├── pdf_extractor_rag.py
│   ├── xml_parser.py
│   └── role_comparer.py
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🤝 Contributing

We welcome contributions! 🚀

1. Fork this repo
2. Create a new branch:

```bash
git checkout -b feature/your-feature-name
```

3. Commit with a clear message:

```bash
git commit -m 'feat: Add new feature'
```

4. Push changes:

```bash
git push origin feature/your-feature-name
```

5. Open a Pull Request!

---

## 📜 License

This project is licensed under the **MIT License**.
See the [LICENSE](./LICENSE) file for full text.

---

## ✉️ Contact / Credits

**Developed by:** \[snsupratim]
🎥 **Video Walkthrough:** [Watch on YouTube](https://youtu.be/zXt7CNc6ov4)
💼 **Connect on LinkedIn:** [LinkedIn Profile](https://www.linkedin.com/in/snsupratim/)

---

Made with 💡 using AI, Python, and a lot of ❤️ for automation.
