# AI Agent Instructions for CHATGPT Project

## Project Overview
This is a Streamlit-based chat application using DeepSeek-V3.1 LLM with MongoDB Atlas for persistence. The application supports multiple chat sessions with separate conversation histories.

## Architecture

### Core Components
- `mainpage.py` - Main Streamlit interface and chat UI
- `initialization.py` - MongoDB and session state initialization
- `chat_fn.py` - Chat history and collection management
- `ai.py` - LLM model initialization and configuration

### Data Flow
1. User messages flow through Streamlit UI (`mainpage.py`)
2. Messages are processed by DeepSeek model (`ai.py`)
3. Conversations are stored in MongoDB collections (`chat_fn.py`)
4. Each chat session has its own collection (e.g., `chat_history_1`, `chat_history_2`)

## Key Patterns and Conventions

### MongoDB Collections
- Collections are named `chat_history_[number]`
- Each new chat creates a new collection
- Messages within a session always stay in their original collection
- Example: `find_collection_for_session()` in `chat_fn.py`

### State Management
- Uses Streamlit session state for UI persistence
- Key state variables:
  - `session_id`: Current chat session identifier
  - `current_collection`: Active MongoDB collection
  - `messages`: Current conversation history
  - `chat_sessions`: List of all chat sessions

### Model Caching
- Model initialization is cached using `@st.cache_resource`
- MongoDB connections are cached for performance
- See `initialize_model()` in `ai.py`

## Development Workflow

### Environment Setup
1. Create `.env` file with:
   ```
   MONGO_URI=your_mongodb_atlas_connection_string
   ```

### Required Dependencies
```python
langchain
langchain-core
langchain-huggingface
transformers
huggingface-hub
python-dotenv
streamlit
pymongo
datetime
```

### Running the Application
```bash
streamlit run mainpage.py
```

## Important Notes
- Always use the chat functions from `chat_fn.py` for message operations
- MongoDB operations should maintain collection isolation
- Use `save_message()` function for storing new messages
- Check collection existence before operations