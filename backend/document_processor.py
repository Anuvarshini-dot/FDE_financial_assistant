"""
Handles loading, chunking, and indexing of finance policy documents into a FAISS vector store.
"""

import os
from pathlib import Path
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


DOCUMENTS_DIR = Path(__file__).parent.parent / "documents"
VECTOR_STORE_DIR = Path(__file__).parent / "vector_store"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def load_documents():
    loader = DirectoryLoader(
        str(DOCUMENTS_DIR),
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    return loader.load()


def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)

    for chunk in chunks:
        source_path = chunk.metadata.get("source", "")
        chunk.metadata["source"] = Path(source_path).name

    return chunks


def build_vector_store(api_key: str) -> FAISS:
    print("Loading documents...")
    docs = load_documents()
    print(f"Loaded {len(docs)} documents.")

    print("Splitting into chunks...")
    chunks = split_documents(docs)
    print(f"Created {len(chunks)} chunks.")

    print("Generating embeddings and building FAISS index...")
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=api_key,
    )
    vector_store = FAISS.from_documents(chunks, embeddings)

    VECTOR_STORE_DIR.mkdir(exist_ok=True)
    vector_store.save_local(str(VECTOR_STORE_DIR))
    print(f"Vector store saved to {VECTOR_STORE_DIR}")

    return vector_store


def load_vector_store(api_key: str) -> FAISS:
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=api_key,
    )
    return FAISS.load_local(
        str(VECTOR_STORE_DIR),
        embeddings,
        allow_dangerous_deserialization=True,
    )


def get_or_build_vector_store(api_key: str) -> FAISS:
    index_file = VECTOR_STORE_DIR / "index.faiss"
    if index_file.exists():
        print("Loading existing vector store...")
        return load_vector_store(api_key)
    return build_vector_store(api_key)
