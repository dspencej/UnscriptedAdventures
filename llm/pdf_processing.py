# llm/pdf_processing.py

import os

from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer

import chromadb
from chromadb.utils import embedding_functions


def process_pdfs(docs_path, chroma_db_path, embedding_model_name):
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=chroma_db_path)

    # Initialize embedding model
    embedding_model = SentenceTransformer(embedding_model_name)
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=embedding_model_name
    )

    collection = client.get_or_create_collection(
        name="dnd_rules", embedding_function=embedding_function
    )

    # Process PDFs
    for filename in os.listdir(docs_path):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(docs_path, filename)
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            # Split text into chunks
            chunks = [text[i : i + 1000] for i in range(0, len(text), 1000)]
            for idx, chunk in enumerate(chunks):
                collection.add(
                    documents=[chunk],
                    metadatas=[{"source": filename}],
                    ids=[f"{filename}-{idx}"],
                )


if __name__ == "__main__":
    DOCS_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "resources")
    )
    CHROMA_DB_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "chromadb")
    )
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Or any other supported model

    process_pdfs(DOCS_PATH, CHROMA_DB_PATH, EMBEDDING_MODEL)
