from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import shutil
import os
import time
import stat
import subprocess

# Global state
_chroma_client = None
_session_initialized = False  # Flag to track if this is first upload in session

def embed_document_for_indexing(processed_document, api_key, chunk_size=1000, chunk_overlap=200):
    """
    Chunk document and setup embedding model in one step.
    Multiple files can be uploaded in same session.
    
    :param processed_document: The processed document text
    :param api_key: OpenAI API key
    :param chunk_size: Size of each chunk
    :param chunk_overlap: Overlap between chunks
    :return: ChromaDB collection
    """
    global _chroma_client, _session_initialized
    
    chroma_path = "./chroma_user_docs"
    
    # Chunk the document
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_text(processed_document)
    print(f"Created {len(chunks)} chunks from document")
    
    # Setup embedding model
    embedding_function = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name= os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    )

    # Only clean up on FIRST upload in this session
    if not _session_initialized:
        print("First upload in this session - cleaning up old data...")
        _session_initialized = True
        
        # Reset client
        _chroma_client = None
        time.sleep(0.5)
        
        # Delete directory
        if os.path.exists(chroma_path):
            print(f"Removing {chroma_path}...")
            try:
                shutil.rmtree(chroma_path)
                print(f"Successfully removed {chroma_path}")
            except Exception as e:
                print(f"Error removing directory: {e}")
                try:
                    subprocess.run(["rm", "-rf", chroma_path], capture_output=True)
                    print("Removed with system command")
                except Exception as e2:
                    print(f"Failed to remove: {e2}")
        
        time.sleep(1)
    else:
        print("Subsequent upload in this session - appending to existing collection...")
    
    # Create or reuse ChromaDB client
    if _chroma_client is None:
        print("Creating ChromaDB client...")
        _chroma_client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        print(f"Created ChromaDB client at {chroma_path}")
    
    # Get or create collection
    try:
        collection = _chroma_client.get_collection(name="chroma_user_docs")
        print("Using existing collection - appending new documents")
    except:
        # Collection doesn't exist, create it
        collection = _chroma_client.create_collection(
            name="chroma_user_docs",
            embedding_function=embedding_function
        )
        print("Created new collection")
    
    # Add documents to collection with unique IDs based on timestamp to avoid duplicates
    import uuid
    doc_id = str(uuid.uuid4())
    chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    
    collection.add(
        documents=chunks,
        ids=chunk_ids
    )
    
    print(f"Successfully indexed {len(chunks)} chunks to ChromaDB")
    return collection


def query_documents(query, k=5, collection_name="chroma_user_docs"):
    """
    Retrieve and format context from the document index.
    
    :param query: The user's question
    :param k: Number of relevant documents to retrieve
    :param collection_name: Name of the collection
    :return: Formatted context string
    """
    global _chroma_client
    
    if _chroma_client is None:
        chroma_path = "./chroma_user_docs"
        if not os.path.exists(chroma_path):
            return "No documents have been indexed yet. Please upload a document first."
        
        _chroma_client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
    
    try:
        vector_index = _chroma_client.get_collection(name=collection_name)
    except Exception as e:
        return f"Error accessing collection: {str(e)}"

    results = vector_index.query(
        query_texts=[query],
        n_results=k
    )
    
    context_chunks = [item for sublist in results['documents'] for item in sublist]
    formatted_context = "\n---\n".join(context_chunks)
    
    return formatted_context
