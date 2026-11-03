import csv
import os
import re
from pathlib import Path
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()
PATH_DB = "../data"
embedding_model = HuggingFaceEmbeddings(model_name=os.getenv('EMBEDDING_MODEL_NAME'), encode_kwargs={"normalize_embeddings":True})


def clean(text: str) -> str:
    # O PDF usa quebras e linhas vazias entre palavras; manter esses separadores
    # fragmenta o texto e prejudica a busca semântica no Chroma.
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_docs() -> list:
    base = Path(PATH_DB)
    documents: list[Document] = []
    for pdf_path in sorted(base.glob("*.pdf")):
        reader = PdfReader(str(pdf_path))
        for page_num, page in enumerate(reader.pages):
            text = clean(page.extract_text()) or ""
            documents.append(
                Document(
                    page_content=text,
                    metadata={"source": str(pdf_path), "page": page_num},
                )
            )
    for csv_path in sorted(base.glob("*.csv")):
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row_num, row in enumerate(csv.DictReader(f)):
                content = "\n".join(f"{k}: {v}" for k, v in row.items())
                documents.append(
                    Document(
                        page_content=content,
                        metadata={"source": str(csv_path), "row": row_num},
                    )
                )
    return documents

def separate_chunks(documents) -> list:
    separator_docs = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=1000,
        length_function=len,
        add_start_index=True
    )
    chunks = separator_docs.split_documents(documents)
    return chunks

def embed_chunks(chunks):
    db = Chroma.from_documents(documents=chunks,embedding=embedding_model,persist_directory="db",
                               collection_metadata={"hnsw:space": "cosine"})
    print("Banco de dados criado")

def create_db():
    docs = load_docs()
    chunks = separate_chunks(docs)
    embed_chunks(chunks)

if __name__ == "__main__":
    create_db()