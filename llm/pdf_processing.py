import os

import chromadb
from chromadb.utils import embedding_functions
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer


def process_pdfs(docs_path, chroma_db_path, collection_name, embedding_model_name):
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=chroma_db_path)

    # Initialize embedding model
    embedding_model = SentenceTransformer(embedding_model_name)
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=embedding_model_name
    )

    # Create or get the collection for the specified agent
    collection = client.get_or_create_collection(
        name=collection_name, embedding_function=embedding_function
    )

    # Process PDFs in the given directory
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
    # Paths for DM and Storyteller resources
    DM_DOCS_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "resources", "dm_resources")
    )
    STORYTELLING_DOCS_PATH = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "resources", "storytelling_resources"
        )
    )

    # ChromaDB paths
    DM_CHROMA_DB_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "chromadb_dm")
    )
    STORYTELLING_CHROMA_DB_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "chromadb_st")
    )

    # Embedding model
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    # Process PDFs for the DM agent
    process_pdfs(DM_DOCS_PATH, DM_CHROMA_DB_PATH, "dm_actions", EMBEDDING_MODEL)

    # Process PDFs for the Storyteller agent
    process_pdfs(
        STORYTELLING_DOCS_PATH,
        STORYTELLING_CHROMA_DB_PATH,
        "story_descriptions",
        EMBEDDING_MODEL,
    )
