# PromotDocAI - Document Q&A Chatbot

A RAG (Retrieval-Augmented Generation) chatbot that allows you to upload documents and have interactive conversations about their content.

## Features

- **Document Upload**: Upload PDF or TXT files for indexing
- **Intelligent Summarization**: Automatic document summarization using GPT-4o
- **Conversational Q&A**: Ask questions about your documents with full conversation history
- **Vector Search**: ChromaDB-powered semantic search across documents
- **Session-based Storage**: Multiple documents can be indexed in a single session
- **Clean State on Restart**: Previous documents are cleared on server restart

## Project Structure

```
promotdoc/
├── main.py                 # Application entry point
├── pyproject.toml          # Project dependencies
├── README.md              # This file
├── .env                   # Environment variables (not committed)
├── .gitignore            # Git ignore rules
├── ui/
│   └── gradio_util.py    # Gradio interface definition
└── utils/
    ├── chat_util.py      # Chat and summarization logic
    ├── chroma_util.py    # ChromaDB indexing and querying
    └── file_reader_util.py # PDF/TXT file processing
```

## Setup

1. **Install dependencies**:
```bash
uv sync
```

2. **Set up environment variables**:
Create a `.env` file with:
```
OPENAI_API_KEY=your_api_key_here
```

## Running the Application

```bash
uv run main.py
```

The Gradio interface will be available at `http://localhost:7860`

## Usage

1. **Upload a Document**: Click the upload button and select a PDF or TXT file
2. **View Summary**: The document summary will appear automatically
3. **Ask Questions**: Type questions in the chat interface to get answers based on the document content
4. **Continue Chat**: Keep asking follow-up questions - the conversation history is maintained
5. **Upload New Document**: Upload another file to add it to the current session's index

## How It Works

- **Document Processing**: Documents are split into 1000-token chunks with 200-token overlap
- **Embeddings**: Text is embedded using OpenAI's `text-embedding-3-small` model
- **Vector Storage**: Embeddings are stored in ChromaDB for fast semantic search
- **Answer Generation**: GPT-4o combines retrieved context with conversation history to generate answers

## Architecture

- **ChromaDB**: Persistent vector database for document embeddings
- **LangChain**: Text splitting and LCEL chains for LLM interactions
- **Gradio**: Web UI for document upload and chat interface
- **OpenAI API**: GPT-4o for summarization and Q&A, text-embedding-3-small for embeddings

## Notes

- Multiple files uploaded in the same session will be indexed together
- Starting a new server session will clean up the previous ChromaDB index
- Conversation history is limited to the last 5 turns to manage token usage
- Retrieved context is passed with each query for accurate answers
