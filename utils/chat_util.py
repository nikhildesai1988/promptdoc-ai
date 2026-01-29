import os
import gradio as gr

from .chroma_util import embed_document_for_indexing, query_documents
from .file_reader_util import process_file
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

# Global variable to track if document is indexed
vector_index = None

def chat_response(message, history):
    """
    Generate a response to user's question using RAG with conversation history.
    
    :param message: User's current message
    :param history: List of previous chat messages [(user_msg, bot_msg), ...]
    :return: AI response string
    """
    global vector_index
    
    if not vector_index:
        return "Please upload and process a document first."
    
    # Retrieve context from vector store
    context = query_documents(message, k=5)
    
    # Build conversation history for the API
    messages = [
        {"role": "system", "content": "You are a helpful assistant answering questions about the uploaded document."}
    ]
    
    # Add previous conversation turns (limit to last 5 to manage tokens)
    if history:
        recent_history = history[-5:] if len(history) > 5 else history
        for turn in recent_history:
            # Handle different history formats from Gradio
            if isinstance(turn, (list, tuple)) and len(turn) == 2:
                user_msg, bot_msg = turn
                messages.append({"role": "user", "content": user_msg})
                messages.append({"role": "assistant", "content": bot_msg})
            elif isinstance(turn, dict):
                # Handle dict format if Gradio uses that
                if "role" in turn and "content" in turn:
                    messages.append(turn)
    
    # Add current message with context
    messages.append({
        "role": "user", 
        "content": f"Context from document:\n{context}\n\nQuestion: {message}"
    })
    
    # Generate streaming response using OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    stream = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        messages=messages,
        temperature=0.7,
        stream=True
    )
    
    # Stream the response
    response_text = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            response_text += chunk.choices[0].delta.content
            yield response_text


def summarize_document(file_input, progress=gr.Progress()):
    """
    Summarize the uploaded document.
    
    :param file_input: Uploaded file
    :return: Summary text
    """
    global vector_index
    
    if not file_input:
        return "Please upload a valid PDF or TXT file."
    
    # Process the uploaded file
    document_content = process_file(file_input)
    print(f"Document Content Length: {len(document_content)} characters")

    if not document_content or "Error" in document_content:
        return document_content
    
    # Embed document and create vector index
    api_key = os.getenv("OPENAI_API_KEY")
    vector_index = embed_document_for_indexing(document_content, api_key=api_key)
    
    # Setup OpenAI client
    client = OpenAI(api_key=api_key)

    stream = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes documents concisely."},
            {"role": "user", "content": f"Summarize the following document content:\n{document_content}"}
        ],
        stream=True
    )
    
    # Stream the summary
    summary_text = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            summary_text += chunk.choices[0].delta.content
            yield summary_text
